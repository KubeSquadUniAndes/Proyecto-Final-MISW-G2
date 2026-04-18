from decimal import Decimal

from src.application.dtos.room_dto import CreateRoomDTO, RoomResponseDTO
from src.domain.entities.room import Room
from src.domain.repositories.room_repository_port import RoomRepositoryPort


class CreateRoomUseCase:
    def __init__(self, room_repo: RoomRepositoryPort) -> None:
        self._repo = room_repo

    async def execute(self, dto: CreateRoomDTO) -> RoomResponseDTO:
        if dto.price < Decimal("0"):
            raise ValueError("Price must be non-negative")
        if dto.capacity < 1:
            raise ValueError("Capacity must be at least 1")
        if dto.size <= 0:
            raise ValueError("Size must be positive")

        room = Room(
            name=dto.name,
            room_type=dto.room_type,
            price=dto.price,
            capacity=dto.capacity,
            beds=dto.beds,
            size=dto.size,
            status=dto.status,
            amenities=dto.amenities,
        )
        saved = await self._repo.save(room)
        return RoomResponseDTO(
            id=saved.id,
            name=saved.name,
            room_type=saved.room_type,
            price=saved.price,
            capacity=saved.capacity,
            beds=saved.beds,
            size=saved.size,
            status=saved.status,
            amenities=saved.amenities,
            created_at=saved.created_at,
            updated_at=saved.updated_at,
        )
