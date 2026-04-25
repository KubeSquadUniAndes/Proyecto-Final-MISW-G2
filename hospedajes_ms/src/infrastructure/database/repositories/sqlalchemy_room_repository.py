from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.room import Room, RoomStatus, RoomType
from src.domain.repositories.room_repository_port import RoomRepositoryPort
from src.infrastructure.database.models.room_model import RoomModel


class SQLAlchemyRoomRepository(RoomRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_domain(self, model: RoomModel) -> Room:
        return Room(
            id=model.id,
            hotel_id=model.hotel_id,
            hotel_name=model.hotel_name,
            destination=model.destination,
            name=model.name,
            room_type=RoomType(model.room_type),
            price=Decimal(str(model.price)),
            capacity=model.capacity,
            beds=model.beds,
            size=float(model.size),
            status=RoomStatus(model.status),
            amenities=model.amenities or "",
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, room: Room) -> RoomModel:
        return RoomModel(
            id=room.id,
            hotel_id=room.hotel_id,
            hotel_name=room.hotel_name,
            destination=room.destination,
            name=room.name,
            room_type=room.room_type,
            price=room.price,
            capacity=room.capacity,
            beds=room.beds,
            size=room.size,
            status=room.status,
            amenities=room.amenities,
            created_at=room.created_at,
            updated_at=room.updated_at,
        )

    async def save(self, room: Room) -> Room:
        model = self._to_model(room)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def get_by_id(self, room_id: UUID) -> Room | None:
        result = await self._session.execute(
            select(RoomModel).where(RoomModel.id == room_id)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list_all(self, hotel_id: UUID | None = None) -> list[Room]:
        query = select(RoomModel).order_by(RoomModel.created_at.desc())
        if hotel_id is not None:
            query = query.where(RoomModel.hotel_id == hotel_id)
        result = await self._session.execute(query)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def search(
        self,
        destination: str | None = None,
        min_capacity: int | None = None,
    ) -> list[Room]:
        query = select(RoomModel).where(RoomModel.status == RoomStatus.DISPONIBLE)
        if destination is not None:
            query = query.where(
                func.lower(RoomModel.destination).contains(destination.lower())
            )
        if min_capacity is not None:
            query = query.where(RoomModel.capacity >= min_capacity)
        result = await self._session.execute(query)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def update(self, room: Room) -> Room:
        result = await self._session.execute(
            select(RoomModel).where(RoomModel.id == room.id)
        )
        model = result.scalar_one_or_none()
        if not model:
            raise ValueError(f"Room {room.id} not found")

        model.name = room.name
        model.room_type = room.room_type
        model.price = room.price
        model.capacity = room.capacity
        model.beds = room.beds
        model.size = room.size
        model.status = room.status
        model.amenities = room.amenities
        model.updated_at = room.updated_at

        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def delete(self, room_id: UUID) -> bool:
        result = await self._session.execute(
            select(RoomModel).where(RoomModel.id == room_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            return False
        await self._session.delete(model)
        await self._session.flush()
        return True

    async def count_by_status(self, status: RoomStatus) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(RoomModel)
            .where(RoomModel.status == status)
        )
        return result.scalar_one()

    async def count_total(self) -> int:
        result = await self._session.execute(
            select(func.count()).select_from(RoomModel)
        )
        return result.scalar_one()
