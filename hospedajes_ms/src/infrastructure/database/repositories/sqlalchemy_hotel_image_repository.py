from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.hotel_image import HotelImage
from src.domain.repositories.hotel_image_repository_port import HotelImageRepositoryPort
from src.infrastructure.database.models.hotel_image_model import HotelImageModel


class SQLAlchemyHotelImageRepository(HotelImageRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_domain(self, model: HotelImageModel) -> HotelImage:
        return HotelImage(
            id=model.id,
            hotel_id=model.hotel_id,
            url=model.url,
            s3_key=model.s3_key,
            created_at=model.created_at,
        )

    async def save(self, image: HotelImage) -> HotelImage:
        model = HotelImageModel(
            id=image.id,
            hotel_id=image.hotel_id,
            url=image.url,
            s3_key=image.s3_key,
            created_at=image.created_at,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def get_by_id(self, image_id: UUID) -> HotelImage | None:
        result = await self._session.execute(
            select(HotelImageModel).where(HotelImageModel.id == image_id)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list_by_hotel(self, hotel_id: UUID) -> list[HotelImage]:
        result = await self._session.execute(
            select(HotelImageModel)
            .where(HotelImageModel.hotel_id == hotel_id)
            .order_by(HotelImageModel.created_at.desc())
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    async def delete(self, image_id: UUID) -> bool:
        result = await self._session.execute(
            select(HotelImageModel).where(HotelImageModel.id == image_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            return False
        await self._session.delete(model)
        await self._session.flush()
        return True
