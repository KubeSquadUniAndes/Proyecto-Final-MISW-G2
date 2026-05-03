from abc import ABC, abstractmethod
from typing import Optional
import uuid

from src.domain.entities.payment import Payment


class PaymentRepositoryPort(ABC):
    @abstractmethod
    async def save(self, payment: Payment) -> Payment:
        pass

    @abstractmethod
    async def find_by_id(self, payment_id: uuid.UUID) -> Optional[Payment]:
        pass

    @abstractmethod
    async def find_by_booking_id(self, booking_id: uuid.UUID) -> Optional[Payment]:
        pass

    @abstractmethod
    async def update(self, payment: Payment) -> Payment:
        pass
