"""Use case: Resend the QR check-in email on traveler request (C5)."""

import logging
from uuid import UUID

from src.domain.entities.booking import BookingStatus
from src.domain.repositories.booking_repository_port import BookingRepositoryPort
from src.infrastructure.clients.notificaciones_client import NotificacionesClient

logger = logging.getLogger(__name__)


class ResendQrEmailUseCase:
    """Resend the QR check-in email to the traveler's registered address.

    Validates:
    - Booking exists and belongs to the requesting user.
    - Booking has a valid QR (CONFIRMED status, qr_is_valid=True, qr_code present).
    - Sends the email via notificaciones_ms; does not modify booking state.
    """

    def __init__(
        self,
        repository: BookingRepositoryPort,
        notificaciones_client: NotificacionesClient,
    ) -> None:
        self._repo = repository
        self._notificaciones_client = notificaciones_client

    async def execute(self, booking_id: UUID, user_id: UUID) -> bool:
        """
        Returns True if the email was sent, False if the email service failed.

        Raises:
            LookupError: Booking not found.
            PermissionError: Booking does not belong to user.
            ValueError: No QR available to send (not yet approved, cancelled, etc.).
        """
        booking = await self._repo.get_by_id(booking_id)
        if not booking:
            raise LookupError(f"Booking {booking_id} not found")

        if booking.user_id != user_id:
            raise PermissionError("Access denied")

        if not booking.qr_code:
            raise ValueError(
                "Esta reserva no tiene un código QR generado. "
                "El QR se genera cuando el hotel confirma la reserva."
            )

        if not booking.qr_is_valid:
            raise ValueError(
                "El código QR de esta reserva ha sido invalidado (reserva cancelada). "
                "No es posible reenviar un QR inválido."
            )

        if booking.status not in (BookingStatus.CONFIRMED, BookingStatus.CHECK_IN):
            raise ValueError(
                f"No se puede reenviar el QR de una reserva con estado '{booking.status.value}'."
            )

        if not booking.traveler_email:
            raise ValueError(
                "No hay correo electrónico registrado para esta reserva. "
                "Actualiza tu perfil con un email válido."
            )

        sent = await self._notificaciones_client.send_qr_checkin_email(
            reservation_code=str(booking.booking_code or booking.id),
            guest_name=booking.traveler_name or "Viajero",
            guest_email=booking.traveler_email,
            property_name="Hotel",
            property_address="Ver detalles en la app",
            check_in=booking.start_time.strftime("%Y-%m-%d"),
            check_out=booking.end_time.strftime("%Y-%m-%d"),
            room_type=booking.room_type or "Habitación estándar",
            num_guests=booking.num_guests,
            qr_code=booking.qr_code,
        )

        if sent:
            logger.info(
                "qr_email_resent booking_id=%s user_id=%s email=%s",
                booking_id,
                user_id,
                booking.traveler_email,
            )
        else:
            logger.error(
                "qr_email_resend_failed booking_id=%s user_id=%s",
                booking_id,
                user_id,
            )

        return sent
