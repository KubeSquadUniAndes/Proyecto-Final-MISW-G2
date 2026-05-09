import logging

from src.application.dtos.payment_voucher_dto import PaymentVoucherDTO, PaymentVoucherResultDTO
from src.infrastructure.channels.payment_voucher_email_channel import send_payment_voucher_email

logger = logging.getLogger(__name__)


class SendPaymentVoucherUseCase:
    async def execute(self, dto: PaymentVoucherDTO) -> PaymentVoucherResultDTO:
        logger.info(
            "sending_payment_voucher reservation_code=%s guest_email=%s transaction_id=%s",
            dto.reservation_code,
            dto.guest_email,
            dto.transaction_id,
        )

        errors: list[str] = []

        email_sent = await send_payment_voucher_email(dto)
        if not email_sent:
            errors.append("email: failed or not configured")

        return PaymentVoucherResultDTO(email_sent=email_sent, errors=errors)
