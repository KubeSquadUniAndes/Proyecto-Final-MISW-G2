import logging

from src.application.dtos.reservation_confirmation_dto import (
    ReservationConfirmationDTO,
    ReservationConfirmationResultDTO,
)
from src.infrastructure.channels.reservation_email_channel import (
    send_reservation_confirmation_email,
)

logger = logging.getLogger(__name__)


class SendReservationConfirmationUseCase:
    async def execute(
        self, dto: ReservationConfirmationDTO
    ) -> ReservationConfirmationResultDTO:
        logger.info(
            "sending_reservation_confirmation reservation_code=%s guest_email=%s",
            dto.reservation_code,
            dto.guest_email,
        )

        errors: list[str] = []

        email_sent = await send_reservation_confirmation_email(dto)
        if not email_sent:
            errors.append("email: failed or not configured")

        return ReservationConfirmationResultDTO(
            email_sent=email_sent,
            errors=errors,
        )
