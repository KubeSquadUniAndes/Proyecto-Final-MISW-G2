import uuid
import httpx

from src.infrastructure.config.settings import settings


class NotificacionesClient:
    def __init__(self):
        self.base_url = settings.NOTIFICACIONES_MS_URL
        self.api_key = settings.INTERNAL_API_KEY

    async def send_payment_confirmation(
        self, booking_id: uuid.UUID, email: str, amount: float, currency: str
    ) -> bool:
        """Trigger email notification for payment confirmation"""
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/v1/notifications/payment-confirmation",
                    json={
                        "booking_id": str(booking_id),
                        "email": email,
                        "amount": amount,
                        "currency": currency,
                    },
                    headers={"X-Internal-API-Key": self.api_key},
                )
                return response.status_code == 200
            except Exception as e:
                print(f"Error sending notification: {e}")
                return False
