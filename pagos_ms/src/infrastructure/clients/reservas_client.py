import uuid
import httpx

from src.infrastructure.config.settings import settings


class ReservasClient:
    def __init__(self):
        self.base_url = settings.RESERVAS_MS_URL
        self.api_key = settings.INTERNAL_API_KEY

    async def update_booking_status(
        self, booking_id: uuid.UUID, status: str, payment_id: uuid.UUID
    ) -> bool:
        """Update booking status to 'confirmed' after successful payment"""
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.patch(
                    f"{self.base_url}/api/v1/bookings/{booking_id}/payment-confirm",
                    json={"status": status, "payment_id": str(payment_id)},
                    headers={"X-Internal-API-Key": self.api_key},
                )
                return response.status_code == 200
            except Exception as e:
                print(f"Error updating booking status: {e}")
                return False
