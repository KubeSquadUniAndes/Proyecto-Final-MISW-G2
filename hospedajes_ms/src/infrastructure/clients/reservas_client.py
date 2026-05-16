import logging
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx

from src.infrastructure.config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class BookingInfo:
    id: str
    status: str
    start_time: datetime
    end_time: datetime


def _parse_dt(value: str) -> datetime:
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


class ReservasClient:
    """HTTP client for reservas_ms booking queries."""

    def __init__(self, base_url: str | None = None) -> None:
        self._base_url = (base_url or settings.RESERVAS_MS_URL).rstrip("/")

    async def get_booking_dates(
        self, booking_ids: list[str], checkin: datetime, checkout: datetime
    ) -> list[BookingInfo]:
        """
        Returns pending/confirmed bookings that overlap [checkin, checkout) for the given IDs.
        Missing IDs are silently omitted by reservas_ms.
        Returns [] on network errors (fail-open).
        """
        if not booking_ids:
            return []

        url = f"{self._base_url}/bookings/bulk-dates"
        payload = {
            "booking_ids": booking_ids,
            "checkin": checkin.isoformat(),
            "checkout": checkout.isoformat(),
        }
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
        except httpx.TimeoutException:
            logger.warning("Timeout fetching bulk booking dates for ids %s", booking_ids)
            return []
        except httpx.HTTPStatusError as exc:
            logger.error(
                "HTTP error fetching bulk booking dates: %s %s",
                exc.response.status_code,
                exc.response.text,
            )
            raise
        except httpx.HTTPError as exc:
            logger.warning("Network error fetching bulk booking dates: %s", exc)
            return []

        bookings = []
        for b in data.get("bookings", []):
            try:
                bookings.append(
                    BookingInfo(
                        id=b["id"],
                        status=b["status"],
                        start_time=_parse_dt(b["start_time"]),
                        end_time=_parse_dt(b["end_time"]),
                    )
                )
            except (KeyError, ValueError) as exc:
                logger.error("Failed to parse booking entry %s: %s", b, exc)
        return bookings
