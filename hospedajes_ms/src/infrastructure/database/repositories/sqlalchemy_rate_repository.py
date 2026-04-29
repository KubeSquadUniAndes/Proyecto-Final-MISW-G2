from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.rate import Rate, SeasonType
from src.domain.entities.room import RoomType
from src.domain.repositories.rate_repository_port import RateRepositoryPort
from src.infrastructure.database.models.rate_model import RateModel


class SQLAlchemyRateRepository(RateRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_domain(self, model: RateModel) -> Rate:
        return Rate(
            id=model.id,
            hotel_id=model.hotel_id,
            room_type=RoomType(model.room_type),
            season=SeasonType(model.season),
            base_price=Decimal(str(model.base_price)),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def save(self, rate: Rate) -> Rate:
        model = RateModel(
            id=rate.id,
            hotel_id=rate.hotel_id,
            room_type=rate.room_type,
            season=rate.season,
            base_price=rate.base_price,
            created_at=rate.created_at,
            updated_at=rate.updated_at,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def get_by_id(self, rate_id: UUID) -> Rate | None:
        result = await self._session.execute(
            select(RateModel).where(RateModel.id == rate_id)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list_by_hotel(
        self, hotel_id: UUID, room_type: RoomType | None = None
    ) -> list[Rate]:
        query = select(RateModel).where(RateModel.hotel_id == hotel_id)
        if room_type is not None:
            query = query.where(RateModel.room_type == room_type)
        result = await self._session.execute(query)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def get_by_hotel_room_type_season(
        self, hotel_id: UUID, room_type: RoomType, season: SeasonType
    ) -> Rate | None:
        result = await self._session.execute(
            select(RateModel).where(
                RateModel.hotel_id == hotel_id,
                RateModel.room_type == room_type,
                RateModel.season == season,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def update(self, rate: Rate) -> Rate:
        result = await self._session.execute(
            select(RateModel).where(RateModel.id == rate.id)
        )
        model = result.scalar_one_or_none()
        if not model:
            raise ValueError(f"Rate {rate.id} not found")
        model.base_price = rate.base_price
        model.updated_at = rate.updated_at
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def delete(self, rate_id: UUID) -> bool:
        result = await self._session.execute(
            select(RateModel).where(RateModel.id == rate_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            return False
        await self._session.delete(model)
        await self._session.flush()
        return True
