import uuid

from fastapi import HTTPException, status

from app.models.reservation import Reservation, ReservationStatus
from app.repositories.base import AbstractReservationRepository
from app.schemas.reservation import ReservationCreate, ReservationUpdate


class ReservationService:
    def __init__(self, repository: AbstractReservationRepository) -> None:
        self._repository = repository

    async def create_reservation(self, data: ReservationCreate) -> Reservation:
        if data.return_date and data.return_date <= data.departure_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="return_date must be after departure_date",
            )
        return await self._repository.create(data)

    async def get_reservation(self, reservation_id: uuid.UUID) -> Reservation:
        reservation = await self._repository.get_by_id(reservation_id)
        if reservation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Reservation {reservation_id} not found",
            )
        return reservation

    async def list_reservations(
        self, skip: int = 0, limit: int = 100
    ) -> tuple[list[Reservation], int]:
        return await self._repository.get_all(skip=skip, limit=limit)

    async def update_reservation(
        self, reservation_id: uuid.UUID, data: ReservationUpdate
    ) -> Reservation:
        existing = await self.get_reservation(reservation_id)

        if existing.status == ReservationStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot modify a cancelled reservation",
            )

        update_dict = data.model_dump(exclude_unset=True)
        if data.status is None and update_dict:
            data = data.model_copy(update={"status": ReservationStatus.MODIFIED})

        result = await self._repository.update(reservation_id, data)
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Reservation {reservation_id} not found",
            )
        return result
