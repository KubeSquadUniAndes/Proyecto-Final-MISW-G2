"""Use case: Check availability for a resource in a date range."""

import logging
from collections import Counter

from src.application.dtos.availability_dto import (
    AvailabilityQueryDTO,
    AvailabilityResponseDTO,
    BookingSummaryDTO,
)
from src.domain.entities.booking import BookingStatus
from src.domain.repositories.booking_repository_port import BookingRepositoryPort

logger = logging.getLogger(__name__)


class CheckAvailabilityUseCase:
    """Check availability by listing bookings in a date range."""

    def __init__(self, repository: BookingRepositoryPort) -> None:
        self._repo = repository

    async def execute(self, dto: AvailabilityQueryDTO) -> AvailabilityResponseDTO:
        """
        Get all bookings for a resource in the specified date range.
        
        Returns bookings that overlap with the query range.
        """
        # Get all bookings for the resource
        all_bookings = await self._repo.get_by_resource_and_date_range(
            resource_id=dto.resource_id,
            start_time=dto.start_time,
            end_time=dto.end_time,
        )

        # Filter by room_type if specified
        if dto.room_type:
            all_bookings = [
                b for b in all_bookings if b.room_type == dto.room_type
            ]

        # Filter by status if specified
        if dto.status:
            all_bookings = [b for b in all_bookings if b.status == dto.status]

        # Build summary DTOs
        booking_summaries = [
            BookingSummaryDTO(
                id=b.id,
                start_time=b.start_time,
                end_time=b.end_time,
                status=b.status,
                status_display=b.status_display,
                room_type=b.room_type,
                num_guests=b.num_guests,
                booking_code=b.booking_code,
                traveler_name=b.traveler_name,
            )
            for b in all_bookings
        ]

        # Count by status
        status_counts = Counter(b.status.value for b in all_bookings)

        logger.info(
            "availability_checked resource_id=%s range=%s-%s total=%d",
            dto.resource_id,
            dto.start_time,
            dto.end_time,
            len(all_bookings),
        )

        return AvailabilityResponseDTO(
            resource_id=dto.resource_id,
            query_range={
                "start_time": dto.start_time.isoformat(),
                "end_time": dto.end_time.isoformat(),
            },
            filters={
                "room_type": dto.room_type,
                "status": dto.status.value if dto.status else None,
            },
            bookings=booking_summaries,
            total_bookings=len(booking_summaries),
            summary={
                "confirmed": status_counts.get(BookingStatus.CONFIRMED.value, 0),
                "pending": status_counts.get(BookingStatus.PENDING.value, 0),
                "cancelled": status_counts.get(BookingStatus.CANCELLED.value, 0),
                "completed": status_counts.get(BookingStatus.COMPLETED.value, 0),
            },
        )
