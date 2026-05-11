import logging
from datetime import datetime
from uuid import UUID

from src.domain.repositories.room_repository_port import RoomRepositoryPort

logger = logging.getLogger(__name__)

_OCCUPY_STATUSES = {"pending", "confirmed"}
_FREE_STATUSES = {"cancelled", "completed"}


class UpdateRoomAvailabilityUseCase:
    def __init__(self, room_repo: RoomRepositoryPort) -> None:
        self._repo = room_repo

    async def execute(
        self,
        room_id: UUID,
        booking_id: str,
        booking_status: str,
        start_time: datetime,
        end_time: datetime,
        trace_id: str = "unknown",
    ) -> None:
        room = await self._repo.get_by_id(room_id)
        if not room:
            logger.warning(
                "availability_update_room_not_found room_id=%s trace_id=%s",
                room_id,
                trace_id,
            )
            return

        if booking_status in _OCCUPY_STATUSES:
            room.add_booking(booking_id)
            logger.info(
                "room_booking_added room_id=%s booking_id=%s new_status=%s trace_id=%s",
                room_id,
                booking_id,
                room.status,
                trace_id,
            )
        elif booking_status in _FREE_STATUSES:
            room.remove_booking(booking_id)
            logger.info(
                "room_booking_removed room_id=%s booking_id=%s new_status=%s trace_id=%s",
                room_id,
                booking_id,
                room.status,
                trace_id,
            )
        else:
            logger.warning(
                "room_availability_unknown_status status=%s room_id=%s trace_id=%s",
                booking_status,
                room_id,
                trace_id,
            )
            return

        await self._repo.update(room)
