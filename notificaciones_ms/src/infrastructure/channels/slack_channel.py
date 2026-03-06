import logging

import httpx

from src.application.dtos.notification_dto import SendNotificationDTO
from src.infrastructure.config.settings import settings

logger = logging.getLogger(__name__)

SEVERITY_EMOJI = {"low": "⚠️", "medium": "🔶", "high": "🚨"}
SEVERITY_COLOR = {"low": "#f39c12", "medium": "#e67e22", "high": "#c0392b"}


async def send_slack(dto: SendNotificationDTO) -> bool:
    """Sends a security alert to a Slack webhook. Returns True on success."""
    if not settings.SLACK_WEBHOOK_URL:
        logger.warning("slack_webhook_not_configured — skipping slack notification")
        return False

    emoji = SEVERITY_EMOJI.get(dto.severity, "⚠️")
    color = SEVERITY_COLOR.get(dto.severity, "#7f8c8d")

    payload = {
        "channel": settings.SLACK_CHANNEL,
        "text": f"{emoji} *Security Alert — Anomalous Booking Detected*",
        "attachments": [
            {
                "color": color,
                "fields": [
                    {"title": "User ID",       "value": str(dto.user_id),    "short": True},
                    {"title": "Booking ID",    "value": str(dto.booking_id), "short": True},
                    {"title": "Anomaly Type",  "value": dto.anomaly_type,    "short": True},
                    {"title": "Severity",      "value": dto.severity.upper(),"short": True},
                    {"title": "Score",         "value": f"{dto.score:.2f} / 1.00", "short": True},
                    {"title": "Detected At",   "value": dto.detected_at.isoformat(), "short": True},
                    {"title": "Description",   "value": dto.description,     "short": False},
                ],
                "footer": "notificaciones_ms",
            }
        ],
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(settings.SLACK_WEBHOOK_URL, json=payload)
            response.raise_for_status()
        logger.info("slack_sent user_id=%s", dto.user_id)
        return True
    except Exception as exc:
        logger.error("slack_error user_id=%s error=%s", dto.user_id, exc)
        return False
