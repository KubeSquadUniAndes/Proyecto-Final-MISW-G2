from datetime import datetime, timezone
from uuid import UUID

from src.application.dtos.room_dto import RoomResponseDTO, UpdateRoomDTO
from src.domain.repositories.room_repository_port import RoomRepositoryPort


class UpdateRoomUseCase:
    def __init__(self, room_repo: RoomRepositoryPort) -> None:
        self._repo = room_repo

    async def execute(self, room_id: UUID, dto: UpdateRoomDTO) -> RoomResponseDTO:
        room = await self._repo.get_by_id(room_id)
        if not room:
            raise ValueError(f"Room {room_id} not found")

        if dto.name is not None:
            room.name = dto.name
        if dto.room_type is not None:
            room.room_type = dto.room_type
        if dto.price is not None:
            room.price = dto.price
        if dto.capacity is not None:
            room.capacity = dto.capacity
        if dto.beds is not None:
            room.beds = dto.beds
        if dto.size is not None:
            room.size = dto.size
        if dto.status is not None:
            room.status = dto.status
        if dto.amenities is not None:
            room.amenities = dto.amenities

        room.updated_at = datetime.now(timezone.utc)
        updated = await self._repo.update(room)
        return RoomResponseDTO(
            id=updated.id,
            hotel_id=updated.hotel_id,
            name=updated.name,
            room_type=updated.room_type,
            price=updated.price,
            capacity=updated.capacity,
            beds=updated.beds,
            size=updated.size,
            status=updated.status,
            amenities=updated.amenities,
            created_at=updated.created_at,
            updated_at=updated.updated_at,
        )
