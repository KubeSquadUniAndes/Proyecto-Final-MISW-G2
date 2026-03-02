from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.refresh_token import RefreshToken
from src.domain.repositories.refresh_token_repository_port import RefreshTokenRepositoryPort
from src.infrastructure.database.models.refresh_token_model import RefreshTokenModel


class SQLAlchemyRefreshTokenRepository(RefreshTokenRepositoryPort):
    """Output adapter: concrete RefreshToken repository using SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_domain(self, model: RefreshTokenModel) -> RefreshToken:
        return RefreshToken(
            id=model.id,
            user_id=model.user_id,
            token=model.token,
            expires_at=model.expires_at,
            revoked=model.revoked,
            created_at=model.created_at,
        )

    async def save(self, token: RefreshToken) -> RefreshToken:
        model = RefreshTokenModel(
            id=token.id,
            user_id=token.user_id,
            token=token.token,
            expires_at=token.expires_at,
            revoked=token.revoked,
            created_at=token.created_at,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def get_by_token(self, token: str) -> RefreshToken | None:
        result = await self._session.execute(
            select(RefreshTokenModel).where(RefreshTokenModel.token == token)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def revoke_by_token(self, token: str) -> bool:
        result = await self._session.execute(
            update(RefreshTokenModel)
            .where(RefreshTokenModel.token == token)
            .values(revoked=True)
        )
        await self._session.flush()
        return result.rowcount > 0

    async def revoke_all_by_user(self, user_id: UUID) -> int:
        result = await self._session.execute(
            update(RefreshTokenModel)
            .where(
                RefreshTokenModel.user_id == user_id,
                RefreshTokenModel.revoked == False,  # noqa: E712
            )
            .values(revoked=True)
        )
        await self._session.flush()
        return result.rowcount
