from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.hotel_image import HotelImage


class HotelImageRepositoryPort(ABC):
    @abstractmethod
    async def save(self, image: HotelImage) -> HotelImage: ...

    @abstractmethod
    async def get_by_id(self, image_id: UUID) -> HotelImage | None: ...

    @abstractmethod
    async def list_by_hotel(self, hotel_id: UUID) -> list[HotelImage]: ...

    @abstractmethod
    async def delete(self, image_id: UUID) -> bool: ...
