from datetime import datetime, timezone

from src.domain.entities.booking import Booking, BookingStatus
from src.domain.repositories.booking_repository_port import BookingRepositoryPort


def _naive(dt: datetime) -> datetime:
    """Strips timezone info to ensure all comparisons use offset-naive datetimes."""
    if dt is None:
        return dt
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


class BookingDomainService:
    """Domain service: contains pure business rules that don't belong to a single entity."""

    def __init__(self, booking_repo: BookingRepositoryPort) -> None:
        self._repo = booking_repo

    async def has_schedule_conflict(
        self,
        user_id,
        resource_id,
        start_time: datetime,
        end_time: datetime,
        exclude_booking_id=None,
    ) -> bool:
        """Checks whether a schedule conflict exists for the same resource."""
        bookings = await self._repo.list_by_user(user_id)

        # Normalize incoming datetimes
        start = _naive(start_time)
        end = _naive(end_time)

        for booking in bookings:
            if exclude_booking_id and booking.id == exclude_booking_id:
                continue
            if booking.resource_id != resource_id:
                continue
            if booking.status in (BookingStatus.CANCELLED, BookingStatus.COMPLETED):
                continue
            # Normalize stored datetimes before comparing
            b_start = _naive(booking.start_time)
            b_end = _naive(booking.end_time)
            # Overlap: start < existing_end AND end > existing_start
            if start < b_end and end > b_start:
                return True
        return False