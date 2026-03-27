from datetime import datetime

from src.application.dtos.auth_dto import RefreshTokenDTO, TokenResponseDTO
from src.application.dtos.jwt_service_port import JWTServicePort
from src.domain.entities.refresh_token import RefreshToken
from src.domain.repositories.refresh_token_repository_port import RefreshTokenRepositoryPort
from src.domain.repositories.user_repository_port import UserRepositoryPort


class RefreshTokenUseCase:
    """Input port: validates a refresh token and issues a new token pair."""

    def __init__(
        self,
        jwt_service: JWTServicePort,
        refresh_token_repo: RefreshTokenRepositoryPort,
        user_repo: UserRepositoryPort,
    ) -> None:
        self._jwt = jwt_service
        self._refresh_repo = refresh_token_repo
        self._user_repo = user_repo

    async def execute(self, dto: RefreshTokenDTO) -> TokenResponseDTO:
        token_entity = await self._refresh_repo.get_by_token(dto.refresh_token)
        if not token_entity or not token_entity.is_valid():
            raise ValueError("Invalid or expired refresh token")

        user = await self._user_repo.get_by_id(token_entity.user_id)
        if not user or not user.is_active():
            raise PermissionError("User account is blocked or inactive")

        # Rotate: revoke old token and issue new pair
        await self._refresh_repo.revoke_by_token(dto.refresh_token)

        access_token = self._jwt.create_access_token(user.id)
        raw_refresh, expires_at = self._jwt.create_refresh_token(user.id)

        new_token = RefreshToken(
            user_id=user.id,
            token=raw_refresh,
            expires_at=expires_at,
        )
        await self._refresh_repo.save(new_token)

        return TokenResponseDTO(
            access_token=access_token,
            refresh_token=raw_refresh,
        )
