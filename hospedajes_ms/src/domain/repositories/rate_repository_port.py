from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.rate import Rate, SeasonType
from src.domain.entities.room import RoomType


class RateRepositoryPort(ABC):
    @abstractmethod
    async def save(self, rate: Rate) -> Rate: ...

    @abstractmethod
    async def get_by_id(self, rate_id: UUID) -> Rate | None: ...

    @abstractmethod
    async def list_by_hotel(
        self, hotel_id: UUID, room_type: RoomType | None = None
    ) -> list[Rate]: ...

    @abstractmethod
    async def get_by_hotel_room_type_season(
        self, hotel_id: UUID, room_type: RoomType, season: SeasonType
    ) -> Rate | None: ...

    @abstractmethod
    async def update(self, rate: Rate) -> Rate: ...

    @abstractmethod
    async def delete(self, rate_id: UUID) -> bool: ...
