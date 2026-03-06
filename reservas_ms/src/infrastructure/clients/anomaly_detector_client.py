"""HTTP client adapter: calls detector_anomalias_ms to analyze bookings."""
import logging
from datetime import datetime
from uuid import UUID

import httpx

from src.infrastructure.config.settings import settings

logger = logging.getLogger(__name__)


class AnomalyDetectorClient:
    """Output adapter: sends booking data to detector_anomalias_ms for analysis."""

    def __init__(self, base_url: str, api_key: str) -> None:
        self._base_url = base_url
        self._api_key = api_key

    async def analyze(
        self,
        user_id: UUID,
        booking_id: UUID,
        resource_id: UUID,
        start_time: datetime,
        end_time: datetime,
    ) -> dict:
        """Sends a booking to the detector. Returns the analysis result dict.
        Never raises — logs errors and returns a safe default on failure.
        """
        url = f"{self._base_url}/api/v1/analysis/booking"
        payload = {
            "user_id": str(user_id),
            "booking_id": str(booking_id),
            "resource_id": str(resource_id),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
        }
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers={"X-Api-Key": self._api_key},
                )
                response.raise_for_status()
                result = response.json()
                if result.get("is_anomalous"):
                    logger.warning(
                        "anomaly_detected booking_id=%s user_id=%s action=%s",
                        booking_id, user_id, result.get("action_taken"),
                    )
                return result
        except httpx.HTTPStatusError as exc:
            logger.error(
                "detector_http_error booking_id=%s status=%s",
                booking_id, exc.response.status_code,
            )
            return {"is_anomalous": False, "error": str(exc)}
        except Exception as exc:
            logger.error("detector_unavailable booking_id=%s error=%s", booking_id, exc)
            return {"is_anomalous": False, "error": str(exc)}
