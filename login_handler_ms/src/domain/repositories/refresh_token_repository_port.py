from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.refresh_token import RefreshToken


class RefreshTokenRepositoryPort(ABC):
    """Output port: defines the contract for RefreshToken persistence."""

    @abstractmethod
    async def save(self, token: RefreshToken) -> RefreshToken: ...

    @abstractmethod
    async def get_by_token(self, token: str) -> RefreshToken | None: ...

    @abstractmethod
    async def revoke_by_token(self, token: str) -> bool: ...

    @abstractmethod
    async def revoke_all_by_user(self, user_id: UUID) -> int:
        """Revokes all active tokens for a user. Returns the count of revoked tokens."""
        ...
