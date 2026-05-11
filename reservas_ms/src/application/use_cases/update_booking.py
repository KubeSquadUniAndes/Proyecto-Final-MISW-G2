import logging
from datetime import datetime

from src.application.dtos.booking_dto import BookingResponseDTO, UpdateBookingDTO
from src.application.use_cases.create_booking import _build_response
from src.domain.repositories.booking_repository_port import BookingRepositoryPort
from src.domain.services.booking_domain_service import BookingDomainService

logger = logging.getLogger(__name__)


class UpdateBookingUseCase:
    def __init__(
        self,
        booking_repo: BookingRepositoryPort,
        domain_service: BookingDomainService,
        anomaly_client=None,
        availability_publisher=None,
    ) -> None:
        self._repo = booking_repo
        self._domain_service = domain_service
        self._anomaly_client = anomaly_client
        self._availability_publisher = availability_publisher

    async def execute(self, dto: UpdateBookingDTO) -> BookingResponseDTO:
        booking = await self._repo.get_by_id(dto.booking_id)
        if not booking:
            raise ValueError(f"Booking {dto.booking_id} not found")

        if booking.user_id != dto.user_id:
            raise PermissionError("You do not have permission to modify this booking")

        if dto.notes is not None:
            booking.notes = dto.notes
        if dto.start_time is not None:
            booking.start_time = dto.start_time
        if dto.end_time is not None:
            booking.end_time = dto.end_time

        booking.updated_at = datetime.utcnow()

        if not booking.is_valid():
            raise ValueError("Updated booking dates are not valid")

        has_conflict = await self._domain_service.has_schedule_conflict(
            user_id=booking.user_id,
            room_id=booking.room_id,
            start_time=booking.start_time,
            end_time=booking.end_time,
            exclude_booking_id=booking.id,
        )
        if has_conflict:
            raise ValueError("Updated dates conflict with an existing booking")

        if self._anomaly_client:
            try:
                result = await self._anomaly_client.analyze(
                    user_id=booking.user_id,
                    booking_id=booking.id,
                    room_id=booking.room_id,
                    start_time=booking.start_time,
                    end_time=booking.end_time,
                )
                if result.get("is_anomalous"):
                    logger.warning(
                        "update_booking_anomaly booking_id=%s action=%s",
                        booking.id,
                        result.get("action_taken"),
                    )
            except Exception as exc:
                logger.error(
                    "anomaly_check_failed booking_id=%s error=%s", booking.id, exc
                )
                raise ValueError("Error anomaly_check_failed")

        updated = await self._repo.update(booking)

        # Publish room availability event (fire-and-forget)
        if self._availability_publisher:
            try:
                from src.domain.events.room_availability_event import (
                    RoomAvailabilityEvent,
                )

                event = RoomAvailabilityEvent(
                    event_type="booking_updated",
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

        return _build_response(updated)
