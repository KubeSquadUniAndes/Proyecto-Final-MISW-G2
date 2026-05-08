import logging

from src.application.dtos.hotel_booking_notification_dto import (
    HotelBookingNotificationDTO,
    HotelBookingNotificationResultDTO,
)
from src.infrastructure.channels.hotel_email_channel import send_hotel_booking_email

logger = logging.getLogger(__name__)


class SendHotelBookingNotificationUseCase:
    async def execute(
        self, dto: HotelBookingNotificationDTO
    ) -> HotelBookingNotificationResultDTO:
        logger.info(
            "sending_hotel_booking_notification booking_code=%s hotel_email=%s",
            dto.booking_code,
            dto.hotel_email,
        )
        errors: list[str] = []
        email_sent = await send_hotel_booking_email(dto)
        if not email_sent:
            errors.append("email: failed or not configured")
        return HotelBookingNotificationResultDTO(email_sent=email_sent, errors=errors)
