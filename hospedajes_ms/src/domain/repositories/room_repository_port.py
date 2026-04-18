from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.room import Room, RoomStatus


class RoomRepositoryPort(ABC):
    @abstractmethod
    async def save(self, room: Room) -> Room: ...

    @abstractmethod
    async def get_by_id(self, room_id: UUID) -> Room | None: ...

    @abstractmethod
    async def list_all(self) -> list[Room]: ...

    @abstractmethod
    async def update(self, room: Room) -> Room: ...

    @abstractmethod
    async def delete(self, room_id: UUID) -> bool: ...

    @abstractmethod
    async def count_by_status(self, status: RoomStatus) -> int: ...

    @abstractmethod
    async def count_total(self) -> int: ...
