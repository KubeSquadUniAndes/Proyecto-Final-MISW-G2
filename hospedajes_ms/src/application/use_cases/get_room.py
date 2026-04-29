from uuid import UUID

from src.application.dtos.room_dto import RoomResponseDTO
from src.domain.repositories.room_repository_port import RoomRepositoryPort


class GetRoomUseCase:
    def __init__(self, room_repo: RoomRepositoryPort) -> None:
        self._repo = room_repo

    async def execute(self, room_id: UUID) -> RoomResponseDTO:
        room = await self._repo.get_by_id(room_id)
        if not room:
            raise ValueError(f"Room {room_id} not found")
        return RoomResponseDTO(
            id=room.id,
            hotel_id=room.hotel_id,
            hotel_name=room.hotel_name,
            name=room.name,
            room_type=room.room_type,
            price=room.price,
            capacity=room.capacity,
            beds=room.beds,
            size=room.size,
            status=room.status,
            amenities=room.amenities,
            created_at=room.created_at,
            updated_at=room.updated_at,
        )
