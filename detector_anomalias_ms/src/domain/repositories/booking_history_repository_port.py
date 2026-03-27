from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID


class BookingHistoryRepositoryPort(ABC):
    """Output port: queries booking history for anomaly feature extraction.

    This port is implemented by an HTTP client adapter that calls reservas_ms,
    keeping the domain free of HTTP concerns.
    """

    @abstractmethod
    async def count_recent_bookings(self, user_id: UUID, since: datetime) -> int:
        """Number of bookings the user made after `since`."""
        ...

    @abstractmethod
    async def count_distinct_resources(self, user_id: UUID, since: datetime) -> int:
        """Number of different resources booked after `since`."""
        ...
