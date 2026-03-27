from src.application.dtos.auth_dto import BlockUserDTO, MessageDTO
from src.domain.repositories.refresh_token_repository_port import RefreshTokenRepositoryPort
from src.domain.repositories.user_repository_port import UserRepositoryPort


class BlockUserUseCase:
    """Input port: blocks a user and revokes all their active tokens.

    Called by detector_anomalias_ms when an anomaly is detected.
    """

    def __init__(
        self,
        user_repo: UserRepositoryPort,
        refresh_token_repo: RefreshTokenRepositoryPort,
    ) -> None:
        self._user_repo = user_repo
        self._refresh_repo = refresh_token_repo

    async def execute(self, dto: BlockUserDTO) -> MessageDTO:
        user = await self._user_repo.get_by_id(dto.user_id)
        if not user:
            raise ValueError(f"User with id={dto.user_id} not found")

        user.block(reason=dto.reason)
        await self._user_repo.update(user)

        # Revoke all active refresh tokens — forces immediate logout
        revoked_count = await self._refresh_repo.revoke_all_by_user(dto.user_id)

        return MessageDTO(
            message=f"User blocked successfully. {revoked_count} active session(s) terminated."
        )
