"""HTTP client adapter: calls login_handler_ms to validate JWT tokens.

On each protected request, reservas_ms calls this client to:
1. Decode the token locally (fast path — no HTTP call needed for signature).
2. Call login_handler_ms GET /api/v1/auth/me to verify the user is not blocked
   (the user could have been blocked after the token was issued).
"""

import logging
from uuid import UUID

import httpx
import jwt


logger = logging.getLogger(__name__)


class LoginHandlerClient:
    """Output adapter: verifies a JWT token and user status against login_handler_ms."""

    def __init__(self, base_url: str, jwt_secret: str, jwt_algorithm: str) -> None:
        self._base_url = base_url
        self._jwt_secret = jwt_secret
        self._jwt_algorithm = jwt_algorithm

    def decode_token_locally(self, token: str) -> dict:
        """Fast local validation — checks signature and expiry without HTTP call.
        Raises ValueError on any failure.
        """
        try:
            payload = jwt.decode(
                token, self._jwt_secret, algorithms=[self._jwt_algorithm]
            )
            if payload.get("type") != "access":
                raise ValueError("Token is not an access token")
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Access token has expired")
        except jwt.InvalidTokenError as exc:
            raise ValueError(f"Invalid token: {exc}")

    async def get_user_status(self, token: str) -> dict:
        """Calls login_handler_ms GET /api/v1/auth/me to check the user is still active.
        Returns the user dict. Raises ValueError if blocked/inactive/unreachable.
        """
        url = f"{self._base_url}/api/v1/auth/me"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    url,
                    headers={"Authorization": f"Bearer {token}"},
                )
                if response.status_code == 401:
                    raise ValueError("Token rejected by login_handler_ms")
                if response.status_code == 403:
                    raise PermissionError("User account is blocked or inactive")
                response.raise_for_status()
                return response.json()
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            logger.error("login_handler_ms unreachable: %s", exc)
            raise ConnectionError(
                "Authentication service is unavailable. Try again later."
            )

    async def validate(self, token: str) -> UUID:
        """Full validation: local decode + remote status check.
        Returns the user_id UUID if valid and active.
        """
        payload = self.decode_token_locally(token)
        user_data = await self.get_user_status(token)

        status = user_data.get("status", "")
        if status == "blocked":
            raise PermissionError("Your account has been blocked. Contact support.")
        if status != "active":
            raise PermissionError(f"Account is not active (status: {status})")

        return UUID(payload["sub"])

    async def validate_with_role(self, token: str) -> dict:
        """Full validation with role extraction.
        Returns dict with user_id and role.
        """
        payload = self.decode_token_locally(token)
        user_data = await self.get_user_status(token)

        status = user_data.get("status", "")
        if status == "blocked":
            raise PermissionError("Your account has been blocked. Contact support.")
        if status != "active":
            raise PermissionError(f"Account is not active (status: {status})")

        return {
            "user_id": UUID(payload["sub"]),
            "role": payload.get("role", "traveler"),
        }
