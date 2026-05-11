import logging
from datetime import datetime, timezone
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

        now = datetime.now(timezone.utc)

        # Normalize naive datetimes that arrive from reservas_ms
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=timezone.utc)

        if booking_status in _OCCUPY_STATUSES:
            if start_time <= now <= end_time:
                room.mark_occupied()
                await self._repo.update(room)
                logger.info(
                    "room_marked_occupied room_id=%s hotel_id=%s trace_id=%s start=%s end=%s",
                    room_id,
                    room.hotel_id,
                    trace_id,
                    start_time.isoformat(),
                    end_time.isoformat(),
                )
            else:
                logger.info(
                    "room_availability_skipped room_id=%s trace_id=%s reason=booking_not_active_now now=%s start=%s end=%s",
                    room_id,
                    trace_id,
                    now.isoformat(),
                    start_time.isoformat(),
                    end_time.isoformat(),
                )
        elif booking_status in _FREE_STATUSES:
            room.mark_available()
            await self._repo.update(room)
            logger.info(
                "room_marked_available room_id=%s hotel_id=%s trace_id=%s",
                room_id,
                room.hotel_id,
                trace_id,
            )
        else:
            logger.warning(
                "room_availability_unknown_status status=%s room_id=%s trace_id=%s",
                booking_status,
                room_id,
                trace_id,
            )
