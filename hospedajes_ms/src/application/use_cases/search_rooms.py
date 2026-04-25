from dataclasses import dataclass
from datetime import datetime

from src.application.dtos.room_dto import RoomResponseDTO
from src.domain.repositories.room_repository_port import RoomRepositoryPort
from src.infrastructure.clients.reservas_client import ReservasClient


@dataclass
class SearchRoomsDTO:
    destination: str | None
    guests: int | None
    checkin: datetime
    checkout: datetime


class SearchRoomsUseCase:
    def __init__(
        self,
        room_repo: RoomRepositoryPort,
        reservas_client: ReservasClient,
    ) -> None:
        self._room_repo = room_repo
        self._reservas_client = reservas_client

    async def execute(self, dto: SearchRoomsDTO) -> list[RoomResponseDTO]:
        if dto.checkin >= dto.checkout:
            raise ValueError("checkin must be before checkout")

        rooms = await self._room_repo.search(
            destination=dto.destination,
            min_capacity=dto.guests,
        )

        available = []
        for room in rooms:
            if await self._reservas_client.is_available(
                room.id, dto.checkin, dto.checkout
            ):
                available.append(
                    RoomResponseDTO(
                        id=room.id,
                        hotel_id=room.hotel_id,
                        hotel_name=room.hotel_name,
                        destination=room.destination,
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
                )

        return available
