import logging
from uuid import UUID

import httpx

from src.domain.entities.anomaly_event import AnomalyEvent
from src.domain.repositories.notification_port import NotificationPort

logger = logging.getLogger(__name__)


class NotificationAdapter(NotificationPort):
    """Output adapter: blocks users via login_handler_ms and sends
    security alerts via notificaciones_ms."""

    def __init__(
        self,
        login_handler_url: str,
        internal_api_key: str,
        notificaciones_ms_url: str,
        notificaciones_api_key: str,
    ) -> None:
        self._login_url = login_handler_url
        self._api_key = internal_api_key
        self._notificaciones_url = notificaciones_ms_url
        self._notificaciones_api_key = notificaciones_api_key

    # ── Block user ────────────────────────────────────────────────────────────

    async def block_user(self, user_id: UUID, reason: str) -> bool:
        url = f"{self._login_url}/api/v1/auth/block-user"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    url,
                    json={"user_id": str(user_id), "reason": reason},
                    headers={"X-Api-Key": self._api_key},
                )
                response.raise_for_status()
                logger.info("block_user_success user_id=%s", user_id)
                return True
        except httpx.HTTPStatusError as exc:
            logger.error(
                "block_user_http_error user_id=%s status=%s body=%s",
                user_id,
                exc.response.status_code,
                exc.response.text,
            )
            return False
        except Exception as exc:
            logger.error("block_user_error user_id=%s error=%s", user_id, exc)
            return False

    # ── Security alert via notificaciones_ms ─────────────────────────────────

    async def send_security_alert_email(self, event: AnomalyEvent) -> bool:
        """Delegates email + Slack alert to notificaciones_ms."""
        url = f"{self._notificaciones_url}/api/v1/notifications/alert"
        payload = {
            "user_id": str(event.user_id),
            "booking_id": str(event.booking_id),
            "anomaly_type": event.anomaly_type.value,
            "severity": event.severity.value,
            "score": event.score,
            "description": event.description,
            "detected_at": event.created_at.isoformat(),
        }
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers={"X-Api-Key": self._notificaciones_api_key},
                )
                response.raise_for_status()
                result = response.json()
                logger.info(
                    "notification_sent user_id=%s email=%s slack=%s errors=%s",
                    event.user_id,
                    result.get("email_sent"),
                    result.get("slack_sent"),
                    result.get("errors"),
                )
                return result.get("email_sent") or result.get("slack_sent")
        except httpx.HTTPStatusError as exc:
            logger.error(
                "notification_http_error user_id=%s status=%s body=%s",
                event.user_id,
                exc.response.status_code,
                exc.response.text,
            )
            return False
        except Exception as exc:
            logger.error("notification_error user_id=%s error=%s", event.user_id, exc)
            return False
