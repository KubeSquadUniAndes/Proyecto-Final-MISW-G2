"""HTTP client adapter: calls notificaciones_ms to send FCM push notifications."""

import logging

import httpx

logger = logging.getLogger(__name__)


class NotificacionesClient:
    """Output adapter: sends booking events to notificaciones_ms for FCM dispatch."""

    def __init__(self, base_url: str, api_key: str) -> None:
        self._base_url = base_url
        self._api_key = api_key

    async def send_booking_notification(
        self,
        fcm_token: str,
        booking_id: str,
        booking_code: str,
        hotel_name: str,
        check_in: str,
        check_out: str,
        status: str,
        event_type: str,
        change_summary: str | None = None,
    ) -> bool:
        """Send a push notification for a booking event.

        Returns True on success. Never raises — logs errors and returns False.
        """
        if not fcm_token:
            logger.warning("fcm_skipped — no token for booking_code=%s", booking_code)
            return False

        url = f"{self._base_url}/api/v1/notifications/booking"
        payload = {
            "fcm_token": fcm_token,
            "booking_id": booking_id,
            "booking_code": booking_code,
            "hotel_name": hotel_name,
            "check_in": check_in,
            "check_out": check_out,
            "status": status,
            "event_type": event_type,
            "change_summary": change_summary,
        }
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers={"x-api-key": self._api_key},
                )
                response.raise_for_status()
                logger.info(
                    "fcm_notification_sent booking_code=%s event=%s",
                    booking_code,
                    event_type,
                )
                return True
        except Exception as exc:
            logger.error(
                "fcm_notification_failed booking_code=%s error=%s",
                booking_code,
                exc,
            )
            return False

    async def notify_hotel_new_booking(
        self,
        hotel_email: str,
        hotel_name: str,
        guest_name: str,
        check_in: str,
        check_out: str,
        num_guests: int,
        booking_code: str,
        room_type: str,
        total_amount: float,
    ) -> bool:
        """Notify hotel via email about a new booking. Never raises."""
        url = f"{self._base_url}/api/v1/notifications/hotel/new-booking"
        payload = {
            "hotel_email": hotel_email,
            "hotel_name": hotel_name,
            "guest_name": guest_name,
            "check_in": check_in,
            "check_out": check_out,
            "num_guests": num_guests,
            "booking_code": booking_code,
            "room_type": room_type,
            "total_amount": total_amount,
        }
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers={"x-api-key": self._api_key},
                )
                response.raise_for_status()
                logger.info("hotel_notification_sent booking_code=%s", booking_code)
                return True
        except Exception as exc:
            logger.error(
                "hotel_notification_failed booking_code=%s error=%s", booking_code, exc
            )
            return False
