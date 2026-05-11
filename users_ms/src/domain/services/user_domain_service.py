from src.domain.repositories.user_repository_port import UserRepositoryPort


class UserDomainService:

    def __init__(self, user_repository: UserRepositoryPort) -> None:
        self._repo = user_repository

    async def email_is_taken(self, email: str) -> bool:
        existing = await self._repo.find_by_email(email)
        return existing is not None
