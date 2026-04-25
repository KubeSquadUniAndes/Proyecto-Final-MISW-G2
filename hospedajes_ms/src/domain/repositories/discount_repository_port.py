from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.rate import Discount


class DiscountRepositoryPort(ABC):
    @abstractmethod
    async def save(self, discount: Discount) -> Discount: ...

    @abstractmethod
    async def get_by_id(self, discount_id: UUID) -> Discount | None: ...

    @abstractmethod
    async def list_by_rate(self, rate_id: UUID) -> list[Discount]: ...

    @abstractmethod
    async def update(self, discount: Discount) -> Discount: ...

    @abstractmethod
    async def delete(self, discount_id: UUID) -> bool: ...
