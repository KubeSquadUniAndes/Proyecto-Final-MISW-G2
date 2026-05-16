"""Use case: Approve a pending booking (hotel admin action)."""

import logging
from datetime import datetime

from src.application.dtos.booking_dto import ApproveBookingDTO, BookingResponseDTO
from src.domain.entities.booking import BookingStatus
from src.domain.ports.room_availability_publisher_port import (
    RoomAvailabilityPublisherPort,
)
from src.domain.repositories.booking_repository_port import BookingRepositoryPort
from src.infrastructure.clients.notificaciones_client import NotificacionesClient

logger = logging.getLogger(__name__)


class ApproveBookingUseCase:
    """Approve a pending booking and trigger payment processing."""

    def __init__(
        self,
        repository: BookingRepositoryPort,
        notificaciones_client: NotificacionesClient | None = None,
        availability_publisher: RoomAvailabilityPublisherPort | None = None,
    ) -> None:
        self._repo = repository
        self._notificaciones_client = notificaciones_client
        self._availability_publisher = availability_publisher

    async def execute(self, dto: ApproveBookingDTO) -> BookingResponseDTO:
        """
        Approve a booking in pending status.

        Raises:
            LookupError: Booking not found
            ValueError: Booking is not in pending status or hold expired
            PermissionError: Admin doesn't have permission (future: validate hotel ownership)
        """
        booking = await self._repo.get_by_id(dto.booking_id)
        if not booking:
            raise LookupError(f"Booking {dto.booking_id} not found")

        # Validate status
        if booking.status != BookingStatus.PENDING:
            raise ValueError(
                f"Cannot approve booking with status '{booking.status}'. "
                "Only pending bookings can be approved."
            )

        # Confirm booking
        booking.confirm()
        updated = await self._repo.update(booking)

        logger.info(
            "booking_approved booking_id=%s admin_id=%s",
            dto.booking_id,
            dto.admin_user_id,
        )

        # Generate QR code for check-in (fire-and-forget — criteria 7)
        try:
            from src.infrastructure.services.qr_generator import generate_booking_qr

            updated.qr_code = generate_booking_qr(
                booking_code=updated.booking_code or str(updated.id),
                booking_id=updated.id,
                guest_name=updated.traveler_name,
                check_in=updated.start_time.strftime("%Y-%m-%d"),
                check_out=updated.end_time.strftime("%Y-%m-%d"),
                room_type=updated.room_type,
            )
            updated.qr_generated_at = datetime.utcnow()
            updated.qr_is_valid = True
            updated = await self._repo.update(updated)
            logger.info("qr_generated booking_id=%s", updated.id)
        except Exception as exc:
            logger.error(
                "qr_generation_failed booking_id=%s error=%s",
                updated.id,
                exc,
            )

        # Publish room availability event (fire-and-forget)
        if self._availability_publisher:
            try:
                from src.domain.events.room_availability_event import (
                    RoomAvailabilityEvent,
                )

                event = RoomAvailabilityEvent(
                    event_type="booking_confirmed",
                    booking_id=updated.id,
                    room_id=updated.room_id,
                    hotel_id=updated.hotel_id,
                    status=updated.status.value,
                    start_time=updated.start_time,
                    end_time=updated.end_time,
                )
                await self._availability_publisher.publish(event)
            except Exception as exc:
                logger.error(
                    "availability_publish_failed booking_id=%s error=%s",
                    updated.id,
                    exc,
                )

        # Send reservation confirmation email
        if self._notificaciones_client and updated.traveler_email:
            logger.info(
                "Sending reservation confirmation email to %s", updated.traveler_email
            )
            await self._notificaciones_client.send_reservation_confirmation(
                reservation_code=str(updated.booking_code or updated.id),
                guest_name=updated.traveler_name or "Guest",
                guest_email=updated.traveler_email,
                property_name="Hotel",
                property_address="Address",
                check_in=updated.start_time.strftime("%Y-%m-%d"),
                check_out=updated.end_time.strftime("%Y-%m-%d"),
                num_guests=updated.num_guests,
                total_amount=float(updated.final_price) if updated.final_price else 0.0,
                property_contact="+57 1 234 5678",
            )
        else:
            logger.warning(
                "Skipping notification: client=%s, email=%s",
                self._notificaciones_client,
                updated.traveler_email,
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
            cancellable=updated.cancellable,
            created_at=updated.created_at,
            updated_at=updated.updated_at,
        )
