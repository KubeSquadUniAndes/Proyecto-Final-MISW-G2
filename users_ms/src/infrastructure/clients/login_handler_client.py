import httpx

from src.infrastructure.config.settings import settings


class LoginHandlerClient:
    """Calls login_handler_ms to create auth credentials after user registration."""

    def __init__(self) -> None:
        self._base_url = settings.LOGIN_HANDLER_MS_URL

    async def register_credentials(
        self,
        email: str,
        password: str,
        full_name: str,
    ) -> None:
        """
        Creates a user entry in login_handler_ms so they can log in.
        Raises RuntimeError if the call fails.
        """
        url = f"{self._base_url}/api/v1/auth/register"
        payload = {
            "email": email,
            "password": password,
            "full_name": full_name,
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)

        if response.status_code == 201:
            return

        if response.status_code == 400:
            detail = response.json().get("detail", "Bad request")
            raise ValueError(f"login_handler_ms rejected registration: {detail}")

        raise RuntimeError(
            f"login_handler_ms returned unexpected status {response.status_code}: {response.text}"
        )
