from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.user import User
from src.domain.repositories.user_repository_port import UserRepositoryPort
from src.infrastructure.database.models.user_model import UserModel


class SQLAlchemyUserRepository(UserRepositoryPort):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, user: User) -> User:
        model = UserModel(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            phone=user.phone,
            country=user.country,
            city=user.city,
            birth_date=user.birth_date,
            hashed_password=user.hashed_password,
            user_type=user.user_type,
            identification_type=user.identification_type,
            identification_number=user.identification_number,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def find_by_email(self, email: str) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.email == email)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_id(self, user_id: UUID) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    @staticmethod
    def _to_entity(model: UserModel) -> User:
        return User(
            id=model.id,
            first_name=model.first_name,
            last_name=model.last_name,
            email=model.email,
            phone=model.phone,
            country=model.country,
            city=model.city,
            birth_date=model.birth_date,
            hashed_password=model.hashed_password,
            user_type=model.user_type,
            identification_type=model.identification_type,
            identification_number=model.identification_number,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )