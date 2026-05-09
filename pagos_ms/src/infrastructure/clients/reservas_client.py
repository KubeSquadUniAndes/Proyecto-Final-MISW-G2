import uuid
import httpx
from typing import Optional

from src.infrastructure.config.settings import settings


class ReservasClient:
    def __init__(self):
        self.base_url = settings.RESERVAS_MS_URL
        self.api_key = settings.INTERNAL_API_KEY

    async def update_booking_status(
        self,
        booking_id: uuid.UUID,
        status: str,
        payment_id: uuid.UUID,
        payment_status: str = "confirmed",
    ) -> bool:
        """Register payment_id and payment_status on the booking. Does NOT change booking status."""
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.patch(
                    f"{self.base_url}/api/v1/bookings/{booking_id}/payment-confirm",
                    json={
                        "status": status,
                        "payment_id": str(payment_id),
                        "payment_status": payment_status,
                    },
                    headers={"X-Internal-API-Key": self.api_key},
                )
                return response.status_code == 200
            except Exception as e:
                print(f"Error updating booking status: {e}")
                return False

    async def get_booking_details(self, booking_id: uuid.UUID) -> Optional[dict]:
        """Fetch booking details for voucher generation. Returns None on failure."""
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/v1/internal/bookings/{booking_id}",
                    headers={"X-Internal-Api-Key": self.api_key},
                )
                if response.status_code == 200:
                    return response.json()
                return None
            except Exception as e:
                print(f"Error fetching booking details: {e}")
                return None
