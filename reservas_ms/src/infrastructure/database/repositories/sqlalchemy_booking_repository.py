from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.booking import Booking, BookingStatus
from src.domain.repositories.booking_repository_port import BookingRepositoryPort
from src.infrastructure.database.models.booking_model import BookingModel


class SQLAlchemyBookingRepository(BookingRepositoryPort):
    """Output adapter: concrete repository implementation using SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # -------------------------------------------------------------------------
    # Domain <-> ORM mappers
    # -------------------------------------------------------------------------

    def _to_domain(self, model: BookingModel) -> Booking:
        return Booking(
            id=model.id,
            user_id=model.user_id,
            resource_id=model.resource_id,
            start_time=model.start_time,
            end_time=model.end_time,
            status=BookingStatus(model.status),
            notes=model.notes,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, booking: Booking) -> BookingModel:
        return BookingModel(
            id=booking.id,
            user_id=booking.user_id,
            resource_id=booking.resource_id,
            start_time=booking.start_time,
            end_time=booking.end_time,
            status=booking.status,
            notes=booking.notes,
            created_at=booking.created_at,
            updated_at=booking.updated_at,
        )

    # -------------------------------------------------------------------------
    # Port implementation
    # -------------------------------------------------------------------------

    async def save(self, booking: Booking) -> Booking:
        model = self._to_model(booking)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def get_by_id(self, booking_id: UUID) -> Booking | None:
        result = await self._session.execute(
            select(BookingModel).where(BookingModel.id == booking_id)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list_by_user(self, user_id: UUID) -> list[Booking]:
        result = await self._session.execute(
            select(BookingModel).where(BookingModel.user_id == user_id)
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    async def update(self, booking: Booking) -> Booking:
        result = await self._session.execute(
            select(BookingModel).where(BookingModel.id == booking.id)
        )
        model = result.scalar_one_or_none()
        if not model:
            raise ValueError(f"Booking with id={booking.id} not found")

        model.status = booking.status
        model.notes = booking.notes
        model.start_time = booking.start_time
        model.end_time = booking.end_time
        model.updated_at = booking.updated_at

        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def delete(self, booking_id: UUID) -> bool:
        result = await self._session.execute(
            select(BookingModel).where(BookingModel.id == booking_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            return False
        await self._session.delete(model)
        await self._session.flush()
        return True
