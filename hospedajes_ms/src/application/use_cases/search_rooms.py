from dataclasses import dataclass
from datetime import datetime, timezone

from src.application.dtos.room_dto import RoomResponseDTO
from src.domain.entities.room import RoomStatus
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

        # Normalize to UTC so reservas_ms gets timezone-aware datetimes
        checkin = (
            dto.checkin.replace(tzinfo=timezone.utc)
            if dto.checkin.tzinfo is None
            else dto.checkin
        )
        checkout = (
            dto.checkout.replace(tzinfo=timezone.utc)
            if dto.checkout.tzinfo is None
            else dto.checkout
        )

        rooms = await self._room_repo.search(
            destination=dto.destination,
            min_capacity=dto.guests,
        )

        available = []
        for room in rooms:
            # Fast path: no bookings at all → always available for any dates
            if room.status == RoomStatus.DISPONIBLE:
                is_avail = True
            else:
                # PARCIAL/OCUPADA: the room has bookings; ask reservas_ms for actual overlap
                is_avail = await self._reservas_client.is_available(
                    room.id, checkin, checkout
                )

            if is_avail:
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
                        booking_ids=room.booking_ids,
                        created_at=room.created_at,
                        updated_at=room.updated_at,
                    )
                )

        return available
