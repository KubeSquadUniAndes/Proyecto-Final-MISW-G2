import logging

from src.application.dtos.qr_checkin_email_dto import (
    QrCancelledEmailDTO,
    QrCheckinEmailDTO,
    QrEmailResultDTO,
)
from src.infrastructure.channels.qr_checkin_email_channel import (
    send_qr_cancelled_email,
    send_qr_checkin_email,
)

logger = logging.getLogger(__name__)


class SendQrCheckinEmailUseCase:
    async def execute(self, dto: QrCheckinEmailDTO) -> QrEmailResultDTO:
        logger.info(
            "sending_qr_checkin_email reservation_code=%s guest_email=%s",
            dto.reservation_code,
            dto.guest_email,
        )
        errors: list[str] = []
        email_sent = await send_qr_checkin_email(dto)
        if not email_sent:
            errors.append("email: failed or not configured")
        return QrEmailResultDTO(email_sent=email_sent, errors=errors)


class SendQrCancelledEmailUseCase:
    async def execute(self, dto: QrCancelledEmailDTO) -> QrEmailResultDTO:
        logger.info(
            "sending_qr_cancelled_email reservation_code=%s guest_email=%s",
            dto.reservation_code,
            dto.guest_email,
        )
        errors: list[str] = []
        email_sent = await send_qr_cancelled_email(dto)
        if not email_sent:
            errors.append("email: failed or not configured")
        return QrEmailResultDTO(email_sent=email_sent, errors=errors)
