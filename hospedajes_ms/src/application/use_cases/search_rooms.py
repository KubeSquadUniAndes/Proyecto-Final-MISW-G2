import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from src.application.dtos.room_dto import RoomResponseDTO
from src.domain.repositories.room_repository_port import RoomRepositoryPort
from src.infrastructure.clients.reservas_client import ReservasClient

logger = logging.getLogger(__name__)


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
            if not room.booking_ids:
                # Fast path: no bookings recorded → always available
                available.append(self._to_dto(room))
                continue

            try:
                bookings = await self._reservas_client.get_booking_dates(
                    room.booking_ids, checkin, checkout
                )
            except Exception as exc:
                logger.error(
                    "Failed to fetch booking dates for room %s: %s", room.id, exc
                )
                # fail-closed: skip room if we can't verify availability
                continue

            if not bookings or not any(
                b.start_time < checkout and b.end_time > checkin
                for b in bookings
            ):
                available.append(self._to_dto(room))

        return available

    @staticmethod
    def _to_dto(room) -> RoomResponseDTO:
        return RoomResponseDTO(
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
