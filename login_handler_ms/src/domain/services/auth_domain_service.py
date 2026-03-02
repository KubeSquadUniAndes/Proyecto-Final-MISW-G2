from src.domain.entities.user import User
from src.domain.repositories.user_repository_port import UserRepositoryPort
from src.domain.services.password_service_port import PasswordServicePort


class AuthDomainService:
    """Domain service: authentication business rules."""

    def __init__(
        self,
        user_repo: UserRepositoryPort,
        password_service: PasswordServicePort,
    ) -> None:
        self._user_repo = user_repo
        self._password_service = password_service

    async def authenticate(self, email: str, plain_password: str) -> User | None:
        """Returns the User if credentials are valid, None otherwise."""
        user = await self._user_repo.get_by_email(email)
        if not user:
            return None
        if not self._password_service.verify(plain_password, user.hashed_password):
            return None
        return user

    async def email_is_taken(self, email: str) -> bool:
        user = await self._user_repo.get_by_email(email)
        return user is not None
