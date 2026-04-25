from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.rate import Discount, DiscountType
from src.domain.repositories.discount_repository_port import DiscountRepositoryPort
from src.infrastructure.database.models.discount_model import DiscountModel


class SQLAlchemyDiscountRepository(DiscountRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_domain(self, model: DiscountModel) -> Discount:
        return Discount(
            id=model.id,
            rate_id=model.rate_id,
            name=model.name,
            discount_type=DiscountType(model.discount_type),
            value=Decimal(str(model.value)),
            start_date=model.start_date,
            end_date=model.end_date,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def save(self, discount: Discount) -> Discount:
        model = DiscountModel(
            id=discount.id,
            rate_id=discount.rate_id,
            name=discount.name,
            discount_type=discount.discount_type,
            value=discount.value,
            start_date=discount.start_date,
            end_date=discount.end_date,
            created_at=discount.created_at,
            updated_at=discount.updated_at,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def get_by_id(self, discount_id: UUID) -> Discount | None:
        result = await self._session.execute(
            select(DiscountModel).where(DiscountModel.id == discount_id)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list_by_rate(self, rate_id: UUID) -> list[Discount]:
        result = await self._session.execute(
            select(DiscountModel).where(DiscountModel.rate_id == rate_id)
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    async def update(self, discount: Discount) -> Discount:
        result = await self._session.execute(
            select(DiscountModel).where(DiscountModel.id == discount.id)
        )
        model = result.scalar_one_or_none()
        if not model:
            raise ValueError(f"Discount {discount.id} not found")
        model.name = discount.name
        model.discount_type = discount.discount_type
        model.value = discount.value
        model.start_date = discount.start_date
        model.end_date = discount.end_date
        model.updated_at = discount.updated_at
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def delete(self, discount_id: UUID) -> bool:
        result = await self._session.execute(
            select(DiscountModel).where(DiscountModel.id == discount_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            return False
        await self._session.delete(model)
        await self._session.flush()
        return True
