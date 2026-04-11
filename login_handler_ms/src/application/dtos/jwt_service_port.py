from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID


class JWTServicePort(ABC):
    """Output port: JWT token generation and validation abstraction."""

    @abstractmethod
    def create_access_token(
        self, user_id: UUID, extra_claims: dict | None = None
    ) -> str: ...

    @abstractmethod
    def create_refresh_token(self, user_id: UUID) -> tuple[str, datetime]:
        """Returns (raw_token_string, expiry_datetime)."""
        ...

    @abstractmethod
    def decode_access_token(self, token: str) -> dict:
        """Returns payload dict. Raises ValueError if invalid or expired."""
        ...

    @abstractmethod
    def decode_refresh_token(self, token: str) -> dict:
        """Returns payload dict. Raises ValueError if invalid or expired."""
        ...
