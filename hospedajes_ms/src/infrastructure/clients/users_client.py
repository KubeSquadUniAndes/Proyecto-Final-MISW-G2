from uuid import UUID

import logging

import httpx

from src.domain.services.hotel_name_service_port import HotelNameServicePort
from src.infrastructure.config.settings import settings

logger = logging.getLogger(__name__)


class UsersClient(HotelNameServicePort):
    async def get_hotel_name(self, hotel_id: UUID) -> str | None:
        url = f"{settings.USERS_MS_URL}/api/v1/users/{hotel_id}"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    url,
                    headers={"X-Internal-Api-Key": settings.INTERNAL_API_KEY},
                )
            if response.status_code == 200:
                data = response.json()
                return f"{data['first_name']} {data['last_name']}"
            logger.warning(
                "users_ms returned %s for hotel_id=%s body=%s",
                response.status_code,
                hotel_id,
                response.text,
            )
        except Exception as exc:
            logger.error("Error calling users_ms for hotel_id=%s: %s", hotel_id, exc)
        return None
