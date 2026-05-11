import httpx

from src.infrastructure.config.settings import settings


class NotificacionesClient:
    def __init__(self):
        self.base_url = settings.NOTIFICACIONES_MS_URL
        self.api_key = settings.NOTIFICACIONES_MS_API_KEY

    async def send_payment_voucher(self, payload: dict) -> bool:
        """Send payment voucher email with PDF to the traveler."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/v1/notifications/payment/voucher",
                    json=payload,
                    headers={"x-api-key": self.api_key},
                )
                return response.status_code == 200
            except Exception as e:
                print(f"Error sending payment voucher: {e}")
                return False
