"""Use case: Process hotel check-in by scanning the booking QR code."""

import logging
from datetime import date

from src.application.dtos.booking_dto import BookingResponseDTO, CheckInBookingDTO
from src.domain.entities.booking import BookingStatus
from src.domain.repositories.booking_repository_port import BookingRepositoryPort
from src.infrastructure.clients.notificaciones_client import NotificacionesClient
from src.infrastructure.clients.users_client import UsersClient

logger = logging.getLogger(__name__)

# Tolerance: check-in allowed on the same calendar day as start_time (UTC).
_CHECKIN_TOLERANCE_DAYS = 0


class CheckInBookingUseCase:
    """Process a QR check-in scan from hotel staff.

    Criteria covered:
    C1 – Validates QR data, transitions CONFIRMED → CHECK_IN, returns full details.
    C2 – Allows check-in only when today == check-in date (same calendar day).
    C3 – Rejects scan when date doesn't match; booking state unchanged.
    C4 – Rejects invalid/expired QR (qr_is_valid=False, or cancelled booking).
    C5 – Detects already-checked-in bookings and reports when it was done.
    C6 – Sends push notification to traveler on success (fire-and-forget).
    C7 – Persists audit fields: timestamp, staff_id, device, IP.
    C8 – DB errors propagate unchanged; use-case state is never partially applied.
    """

    def __init__(
        self,
        repository: BookingRepositoryPort,
        notificaciones_client: NotificacionesClient | None = None,
        users_client: UsersClient | None = None,
    ) -> None:
        self._repo = repository
        self._notificaciones_client = notificaciones_client
        self._users_client = users_client

    async def execute(self, dto: CheckInBookingDTO) -> BookingResponseDTO:
        """
        Raises:
            LookupError: Booking not found.
            ValueError: QR invalid, date mismatch, already checked-in, wrong state.
        """
        booking = await self._repo.get_by_id(dto.booking_id)
        if not booking:
            raise LookupError(f"Booking {dto.booking_id} not found")

        # Validate booking_code matches QR payload (extra tamper check)
        if booking.booking_code and booking.booking_code != dto.booking_code:
            raise ValueError(
                "El código QR no corresponde a esta reserva. "
                f"Esperado: {booking.booking_code}, recibido: {dto.booking_code}"
            )

        # C5 – Already checked in
        if booking.status == BookingStatus.CHECK_IN:
            ts = (
                booking.checked_in_at.strftime("%Y-%m-%d %H:%M:%S UTC")
                if booking.checked_in_at
                else "desconocida"
            )
            raise ValueError(f"El check-in ya fue registrado previamente el {ts}.")

        # C4 – Cancelled or explicitly invalidated QR
        if booking.status == BookingStatus.CANCELLED:
            raise ValueError("El código QR no es válido: la reserva fue cancelada.")

        if not booking.qr_is_valid:
            raise ValueError(
                "El código QR está invalidado. "
                "Motivo: la reserva fue modificada o cancelada."
            )

        # C4 – QR must exist (only generated on approval)
        if not booking.qr_code:
            raise ValueError(
                "Esta reserva no tiene un código QR generado. "
                "Solo las reservas confirmadas por el hotel tienen QR de check-in."
            )

        # Only CONFIRMED bookings can proceed past this point
        if booking.status != BookingStatus.CONFIRMED:
            raise ValueError(
                f"No se puede realizar check-in de una reserva con estado '{booking.status.value}'. "
                "Solo las reservas confirmadas pueden hacer check-in."
            )

        # C2 / C3 – Date validation (same calendar day, UTC)
        today = date.today()
        checkin_date = booking.start_time.date()
        if today < checkin_date:
            raise ValueError(
                f"El check-in aún no está disponible. "
                f"La fecha de llegada es {checkin_date.isoformat()}."
            )
        if today > checkin_date:
            raise ValueError(
                f"El código QR ha expirado. "
                f"La fecha de check-in registrada fue {checkin_date.isoformat()} "
                f"y la fecha actual es {today.isoformat()}."
            )

        # C1 / C7 – Transition to CHECK_IN with audit data
        booking.check_in(
            staff_id=dto.staff_id,
            device=dto.device,
            ip=dto.ip,
        )
        updated = await self._repo.update(booking)

        logger.info(
            "checkin_completed booking_id=%s booking_code=%s staff=%s ip=%s",
            updated.id,
            updated.booking_code,
            dto.staff_id,
            dto.ip,
        )

        # C6 – Push notification (fire-and-forget)
        if self._users_client and self._notificaciones_client:
            try:
                fcm_token = await self._users_client.get_fcm_token(updated.user_id)
                if fcm_token:
                    await self._notificaciones_client.send_booking_notification(
                        fcm_token=fcm_token,
                        booking_id=str(updated.id),
                        booking_code=updated.booking_code or "",
                        hotel_name=str(updated.hotel_id),
                        check_in=updated.start_time.strftime("%Y-%m-%d"),
                        check_out=updated.end_time.strftime("%Y-%m-%d"),
                        status=updated.status_display,
                        event_type="checkin",
                        change_summary=(
                            "Tu check-in fue registrado exitosamente. "
                            f"Bienvenido, {updated.traveler_name or 'viajero'}. "
                            f"Habitación: {updated.room_type or 'ver recepción'}."
                        ),
                    )
            except Exception as exc:
                logger.error(
                    "checkin_notification_failed booking_id=%s error=%s",
                    updated.id,
                    exc,
                )

        return BookingResponseDTO(
            id=updated.id,
            user_id=updated.user_id,
            hotel_id=updated.hotel_id,
            room_id=updated.room_id,
            start_time=updated.start_time,
            end_time=updated.end_time,
            status=updated.status,
            status_display=updated.status_display,
            notes=updated.notes,
            booking_code=updated.booking_code,
            room_type=updated.room_type,
            num_guests=updated.num_guests,
            additional_guests=updated.additional_guests,
            special_requests=updated.special_requests,
            price_per_night=updated.price_per_night,
            total_nights=updated.total_nights,
            total_price=updated.total_price,
            taxes=updated.taxes,
            final_price=updated.final_price,
            traveler_name=updated.traveler_name,
            traveler_email=updated.traveler_email,
            traveler_phone=updated.traveler_phone,
            traveler_document=updated.traveler_document,
            qr_code=updated.qr_code,
            qr_generated_at=updated.qr_generated_at,
            qr_is_valid=updated.qr_is_valid,
            checked_in_at=updated.checked_in_at,
            checkin_staff_id=updated.checkin_staff_id,
            cancellable=updated.cancellable,
            created_at=updated.created_at,
            updated_at=updated.updated_at,
        )
