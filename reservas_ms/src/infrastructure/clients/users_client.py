"""HTTP client adapter: calls users_ms to get FCM token for a user."""

import logging
from uuid import UUID

import httpx

logger = logging.getLogger(__name__)


class UsersClient:
    """Output adapter: fetches user FCM token from users_ms."""

    def __init__(self, base_url: str, api_key: str) -> None:
        self._base_url = base_url
        self._api_key = api_key

    async def get_fcm_token(self, user_id: UUID) -> str | None:
        """Returns the FCM token for a user, or None if not found/unavailable."""
        url = f"{self._base_url}/api/v1/users/{user_id}/fcm-token"
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(
                    url,
                    headers={"X-Internal-Api-Key": self._api_key},
                )
                if response.status_code == 200:
                    return response.json().get("fcm_token")
                return None
        except Exception as exc:
            logger.warning(
                "users_ms_fcm_token_unavailable user_id=%s error=%s",
                user_id,
                exc,
            )
            return None

    async def get_user_email(self, user_id: UUID) -> str | None:
        """Returns the email for a user from login-handler, or None."""
        from src.infrastructure.config.settings import settings as s

        url = f"{s.LOGIN_HANDLER_MS_URL}/api/v1/auth/users/{user_id}/email"
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(
                    url,
                    headers={"X-Api-Key": self._api_key},
                )
                if response.status_code == 200:
                    return response.json().get("email")
                return None
        except Exception as exc:
            logger.warning(
                "login_handler_email_unavailable user_id=%s error=%s", user_id, exc
            )
            return None
