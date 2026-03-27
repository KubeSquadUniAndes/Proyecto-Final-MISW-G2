"""HTTP client adapter: queries reservas_ms for booking history.

For the experiment, this returns stub values (0) so the random sampler
is the primary anomaly trigger. Wire up a real httpx client when
reservas_ms exposes the required query endpoints.
"""
import logging
from datetime import datetime
from uuid import UUID

from src.domain.repositories.booking_history_repository_port import BookingHistoryRepositoryPort

logger = logging.getLogger(__name__)


class ReservasMsBookingHistoryClient(BookingHistoryRepositoryPort):
    """Output adapter: fetches booking history from reservas_ms via HTTP.

    Stub implementation — returns 0 for all queries.
    Replace with real httpx calls when reservas_ms exposes history endpoints.
    """

    def __init__(self, base_url: str, api_key: str) -> None:
        self._base_url = base_url
        self._api_key = api_key

    async def count_recent_bookings(self, user_id: UUID, since: datetime) -> int:
        # TODO: GET {base_url}/api/v1/bookings/?user_id={user_id}&since={since}
        logger.debug("stub: count_recent_bookings user_id=%s since=%s", user_id, since)
        return 0

    async def count_distinct_resources(self, user_id: UUID, since: datetime) -> int:
        # TODO: GET {base_url}/api/v1/bookings/distinct-resources?user_id={user_id}&since={since}
        logger.debug("stub: count_distinct_resources user_id=%s since=%s", user_id, since)
        return 0
