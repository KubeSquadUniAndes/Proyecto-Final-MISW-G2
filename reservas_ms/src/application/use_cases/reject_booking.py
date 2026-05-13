"""Use case: Reject a pending booking (hotel admin action)."""

import logging

from src.application.dtos.booking_dto import BookingResponseDTO, RejectBookingDTO
from src.domain.entities.booking import BookingStatus
from src.domain.ports.room_availability_publisher_port import (
    RoomAvailabilityPublisherPort,
)
from src.domain.repositories.booking_repository_port import BookingRepositoryPort

logger = logging.getLogger(__name__)


class RejectBookingUseCase:
    """Reject a pending booking and release inventory."""

    def __init__(
        self,
        repository: BookingRepositoryPort,
        availability_publisher: RoomAvailabilityPublisherPort | None = None,
    ) -> None:
        self._repo = repository
        self._availability_publisher = availability_publisher

    async def execute(self, dto: RejectBookingDTO) -> BookingResponseDTO:
        """
        Reject a booking in pending status.

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
                f"Cannot reject booking with status '{booking.status}'. "
                "Only pending bookings can be rejected."
            )

        # TODO: Validate hold expiration (if hold_until field exists)
        # if booking.hold_until and datetime.utcnow() > booking.hold_until:
        #     raise ValueError("Booking hold has expired")

        # TODO: Validate admin has permission over the property
        # This would require checking if admin_user_id owns/manages hotel_id

        # Reject booking (changes status to CANCELLED)
        booking.reject()

        # Store rejection reason in notes
        rejection_note = f"[REJECTED by admin] {dto.rejection_reason}"
        if booking.notes:
            booking.notes = f"{booking.notes}\n{rejection_note}"
        else:
            booking.notes = rejection_note

        updated = await self._repo.update(booking)

        logger.info(
            "booking_rejected booking_id=%s admin_id=%s reason=%s",
            dto.booking_id,
            dto.admin_user_id,
            dto.rejection_reason,
        )

        # Publish room availability event to release the room (fire-and-forget)
        if self._availability_publisher:
            try:
                from src.domain.events.room_availability_event import (
                    RoomAvailabilityEvent,
                )

                event = RoomAvailabilityEvent(
                    event_type="booking_rejected",
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
                    "availability_publish_failed booking_id=%s error=%s", updated.id, exc
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
            cancellable=updated.cancellable,
            created_at=updated.created_at,
            updated_at=updated.updated_at,
        )
