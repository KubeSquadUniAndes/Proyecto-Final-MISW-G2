import logging

from src.application.dtos.notification_dto import (
    BookingNotificationDTO,
    BookingNotificationResultDTO,
)
from src.infrastructure.channels.fcm_channel import send_fcm

logger = logging.getLogger(__name__)

TITLES = {
    "created": "✅ Reserva creada",
    "status_changed": "🔔 Estado de reserva actualizado",
    "modified": "✏️ Reserva modificada",
}


class SendBookingNotificationUseCase:
    """Sends a push notification to the traveler's device via FCM."""

    async def execute(
        self, dto: BookingNotificationDTO
    ) -> BookingNotificationResultDTO:
        title = TITLES.get(dto.event_type, "TravelHub — Reserva")
        body = self._build_body(dto)

        logger.info(
            "sending_booking_notification booking_code=%s event=%s",
            dto.booking_code,
            dto.event_type,
        )

        errors: list[str] = []
        fcm_sent = await send_fcm(
            fcm_token=dto.fcm_token,
            title=title,
            body=body,
            data={
                "booking_id": dto.booking_id,
                "booking_code": dto.booking_code,
                "event_type": dto.event_type,
            },
        )

        if not fcm_sent:
            errors.append("fcm: failed or not configured")

        return BookingNotificationResultDTO(fcm_sent=fcm_sent, errors=errors)

    @staticmethod
    def _build_body(dto: BookingNotificationDTO) -> str:
        if dto.event_type == "created":
            return (
                f"Reserva {dto.booking_code} en {dto.hotel_name}\n"
                f"Check-in: {dto.check_in} — Check-out: {dto.check_out}\n"
                f"Estado: {dto.status}"
            )
        if dto.event_type == "status_changed":
            return (
                f"Reserva {dto.booking_code} en {dto.hotel_name}\n"
                f"Nuevo estado: {dto.status}"
            )
        summary = dto.change_summary or "Datos actualizados"
        return f"Reserva {dto.booking_code} en {dto.hotel_name}\n" f"{summary}"
