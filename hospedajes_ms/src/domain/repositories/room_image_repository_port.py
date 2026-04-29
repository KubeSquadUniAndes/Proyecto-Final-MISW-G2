from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.room_image import RoomImage


class RoomImageRepositoryPort(ABC):
    @abstractmethod
    async def save(self, image: RoomImage) -> RoomImage: ...

    @abstractmethod
    async def get_by_id(self, image_id: UUID) -> RoomImage | None: ...

    @abstractmethod
    async def list_by_room(self, room_id: UUID) -> list[RoomImage]: ...

    @abstractmethod
    async def delete(self, image_id: UUID) -> bool: ...
