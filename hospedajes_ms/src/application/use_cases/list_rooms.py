from src.application.dtos.room_dto import RoomResponseDTO
from src.domain.repositories.room_repository_port import RoomRepositoryPort


class ListRoomsUseCase:
    def __init__(self, room_repo: RoomRepositoryPort) -> None:
        self._repo = room_repo

    async def execute(self) -> list[RoomResponseDTO]:
        rooms = await self._repo.list_all()
        return [
            RoomResponseDTO(
                id=r.id,
                name=r.name,
                room_type=r.room_type,
                price=r.price,
                capacity=r.capacity,
                beds=r.beds,
                size=r.size,
                status=r.status,
                amenities=r.amenities,
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
            for r in rooms
        ]
