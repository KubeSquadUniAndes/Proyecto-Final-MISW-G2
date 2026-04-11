from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.user import User


class UserRepositoryPort(ABC):
    """Output port: defines the contract any User repository implementation must fulfill."""

    @abstractmethod
    async def save(self, user: User) -> User: ...

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> User | None: ...

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    async def update(self, user: User) -> User: ...

    @abstractmethod
    async def delete(self, user_id: UUID) -> bool: ...
