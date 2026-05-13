import logging

from src.application.dtos.booking_dto import BookingResponseDTO, CancelBookingDTO
from src.domain.ports.room_availability_publisher_port import (
    RoomAvailabilityPublisherPort,
)
from src.domain.repositories.booking_repository_port import BookingRepositoryPort

logger = logging.getLogger(__name__)


class CancelBookingUseCase:
    def __init__(
        self,
        booking_repo: BookingRepositoryPort,
        availability_publisher: RoomAvailabilityPublisherPort | None = None,
    ) -> None:
        self._repo = booking_repo
        self._availability_publisher = availability_publisher

    async def execute(self, dto: CancelBookingDTO) -> BookingResponseDTO:
        # 1. Load booking
        booking = await self._repo.get_by_id(dto.booking_id)
        if not booking:
            raise LookupError(f"Booking {dto.booking_id} not found")

        # 2. Verify ownership
        if booking.user_id != dto.user_id:
            raise PermissionError("You do not have permission to cancel this booking")

        # 3. Verify cancellable state
        if not booking.cancellable:
            raise ValueError(f"Cannot cancel a booking with status '{booking.status}'")

        # 4. Cancel and persist
        booking.cancel()
        updated = await self._repo.update(booking)

        # 5. Publish room availability event (fire-and-forget)
        if self._availability_publisher:
            try:
                from src.domain.events.room_availability_event import (
                    RoomAvailabilityEvent,
                )

                event = RoomAvailabilityEvent(
                    event_type="booking_cancelled",
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

        from src.application.use_cases.create_booking import _build_response

        return _build_response(updated)
