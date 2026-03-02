from uuid import UUID

from src.application.dtos.auth_dto import UserResponseDTO
from src.domain.repositories.user_repository_port import UserRepositoryPort


class GetMeUseCase:
    """Input port: returns the authenticated user's profile."""

    def __init__(self, user_repo: UserRepositoryPort) -> None:
        self._user_repo = user_repo

    async def execute(self, user_id: UUID) -> UserResponseDTO:
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        return UserResponseDTO(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            status=user.status,
            is_superuser=user.is_superuser,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
