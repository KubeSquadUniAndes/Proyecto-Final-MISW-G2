import logging

from src.application.dtos.notification_dto import (
    NotificationResultDTO,
    SendNotificationDTO,
)
from src.infrastructure.channels.email_channel import send_email
from src.infrastructure.channels.slack_channel import send_slack

logger = logging.getLogger(__name__)


class SendNotificationUseCase:
    """Sends an anomaly alert via all configured channels (email + Slack).
    Both channels are attempted regardless of the other's result.
    """

    async def execute(self, dto: SendNotificationDTO) -> NotificationResultDTO:
        logger.warning(
            "sending_alert user_id=%s booking_id=%s anomaly=%s severity=%s score=%.2f",
            dto.user_id,
            dto.booking_id,
            dto.anomaly_type,
            dto.severity,
            dto.score,
        )

        errors: list[str] = []

        email_sent = await send_email(dto)
        if not email_sent:
            errors.append("email: failed or not configured")

        slack_sent = await send_slack(dto)
        if not slack_sent:
            errors.append("slack: failed or not configured")

        return NotificationResultDTO(
            email_sent=email_sent,
            slack_sent=slack_sent,
            errors=errors,
        )
