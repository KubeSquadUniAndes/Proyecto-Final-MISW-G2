from abc import ABC, abstractmethod
from uuid import UUID


class HotelNameServicePort(ABC):
    @abstractmethod
    async def get_hotel_name(self, hotel_id: UUID) -> str | None: ...
