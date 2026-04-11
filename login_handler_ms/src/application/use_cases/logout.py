from src.application.dtos.auth_dto import MessageDTO, RefreshTokenDTO
from src.domain.repositories.refresh_token_repository_port import (
    RefreshTokenRepositoryPort,
)


class LogoutUseCase:
    """Input port: revokes the refresh token on logout."""

    def __init__(self, refresh_token_repo: RefreshTokenRepositoryPort) -> None:
        self._refresh_repo = refresh_token_repo

    async def execute(self, dto: RefreshTokenDTO) -> MessageDTO:
        token = await self._refresh_repo.get_by_token(dto.refresh_token)
        if not token:
            raise ValueError("Refresh token not found")

        await self._refresh_repo.revoke_by_token(dto.refresh_token)
        return MessageDTO(message="Logged out successfully")
