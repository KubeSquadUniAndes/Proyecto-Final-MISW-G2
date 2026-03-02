import uuid
from abc import ABC, abstractmethod
from typing import Optional

from app.models.reservation import Reservation
from app.schemas.reservation import ReservationCreate, ReservationUpdate


class AbstractReservationRepository(ABC):
    @abstractmethod
    async def create(self, data: ReservationCreate) -> Reservation: ...

    @abstractmethod
    async def get_by_id(self, reservation_id: uuid.UUID) -> Optional[Reservation]: ...

    @abstractmethod
    async def get_all(
        self, skip: int = 0, limit: int = 100
    ) -> tuple[list[Reservation], int]: ...

    @abstractmethod
    async def update(
        self, reservation_id: uuid.UUID, data: ReservationUpdate
    ) -> Optional[Reservation]: ...
