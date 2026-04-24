from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.booking import Booking


class BookingRepositoryPort(ABC):
    """Output port: defines the contract any Booking repository implementation must fulfill."""

    @abstractmethod
    async def save(self, booking: Booking) -> Booking: ...

    @abstractmethod
    async def get_by_id(self, booking_id: UUID) -> Booking | None: ...

    @abstractmethod
    async def list_by_user(self, user_id: UUID) -> list[Booking]: ...

    @abstractmethod
    async def get_active_by_user(self, user_id: UUID) -> list[Booking]: ...

    @abstractmethod
    async def update(self, booking: Booking) -> Booking: ...

    @abstractmethod
    async def delete(self, booking_id: UUID) -> bool: ...

    @abstractmethod
    async def get_by_room_and_date_range(
        self, room_id: UUID, start_time, end_time
    ) -> list[Booking]: ...

    @abstractmethod
    async def list_by_hotel(self, hotel_id: UUID) -> list[Booking]: ...
