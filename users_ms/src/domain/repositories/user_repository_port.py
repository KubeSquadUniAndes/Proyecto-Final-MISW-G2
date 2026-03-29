from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.user import User


class UserRepositoryPort(ABC):

    @abstractmethod
    async def save(self, user: User) -> User:
        raise NotImplementedError

    @abstractmethod
    async def find_by_email(self, email: str) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def find_by_id(self, user_id: UUID) -> User | None:
        raise NotImplementedError
