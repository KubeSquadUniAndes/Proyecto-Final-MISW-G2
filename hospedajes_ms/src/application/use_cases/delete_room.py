from uuid import UUID

from src.domain.repositories.room_repository_port import RoomRepositoryPort


class DeleteRoomUseCase:
    def __init__(self, room_repo: RoomRepositoryPort) -> None:
        self._repo = room_repo

    async def execute(self, room_id: UUID) -> None:
        deleted = await self._repo.delete(room_id)
        if not deleted:
            raise ValueError(f"Room {room_id} not found")
