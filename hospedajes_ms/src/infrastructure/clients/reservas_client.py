from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

import httpx

from src.infrastructure.config.settings import settings

# Statuses that block availability
_BLOCKING_STATUSES = {"pending", "confirmed"}


@dataclass
class BookingInfo:
    id: str
    status: str
    start_time: str
    end_time: str


class ReservasClient:
    """HTTP client for reservas_ms availability checks."""

    def __init__(self, base_url: str | None = None) -> None:
        self._base_url = (base_url or settings.RESERVAS_MS_URL).rstrip("/")

    async def is_available(
        self,
        room_id: UUID,
        checkin: datetime,
        checkout: datetime,
    ) -> bool:
        """
        Returns True if the room has no pending/confirmed bookings
        overlapping the given date range.
        """
        url = f"{self._base_url}/bookings/availability"
        params = {
            "room_id": str(room_id),
            "start_time": checkin.isoformat(),
            "end_time": checkout.isoformat(),
        }
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError:
            # If reservas_ms is unreachable, treat room as available (fail open)
            return True

        bookings = data.get("bookings", [])
        blocking = [b for b in bookings if b.get("status") in _BLOCKING_STATUSES]
        return len(blocking) == 0
