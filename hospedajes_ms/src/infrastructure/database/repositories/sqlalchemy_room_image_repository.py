from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.room_image import RoomImage
from src.domain.repositories.room_image_repository_port import RoomImageRepositoryPort
from src.infrastructure.database.models.room_image_model import RoomImageModel


class SQLAlchemyRoomImageRepository(RoomImageRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_domain(self, model: RoomImageModel) -> RoomImage:
        return RoomImage(
            id=model.id,
            room_id=model.room_id,
            url=model.url,
            s3_key=model.s3_key,
            created_at=model.created_at,
        )

    async def save(self, image: RoomImage) -> RoomImage:
        model = RoomImageModel(
            id=image.id,
            room_id=image.room_id,
            url=image.url,
            s3_key=image.s3_key,
            created_at=image.created_at,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def get_by_id(self, image_id: UUID) -> RoomImage | None:
        result = await self._session.execute(
            select(RoomImageModel).where(RoomImageModel.id == image_id)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list_by_room(self, room_id: UUID) -> list[RoomImage]:
        result = await self._session.execute(
            select(RoomImageModel)
            .where(RoomImageModel.room_id == room_id)
            .order_by(RoomImageModel.created_at.desc())
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    async def delete(self, image_id: UUID) -> bool:
        result = await self._session.execute(
            select(RoomImageModel).where(RoomImageModel.id == image_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            return False
        await self._session.delete(model)
        await self._session.flush()
        return True
