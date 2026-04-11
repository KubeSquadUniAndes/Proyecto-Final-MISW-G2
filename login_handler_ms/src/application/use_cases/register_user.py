from src.application.dtos.auth_dto import RegisterUserDTO, UserResponseDTO
from src.domain.entities.user import User
from src.domain.repositories.user_repository_port import UserRepositoryPort
from src.domain.services.auth_domain_service import AuthDomainService
from src.domain.services.password_service_port import PasswordServicePort


class RegisterUserUseCase:
    """Input port: handles new user registration."""

    def __init__(
        self,
        user_repo: UserRepositoryPort,
        auth_domain_service: AuthDomainService,
        password_service: PasswordServicePort,
    ) -> None:
        self._user_repo = user_repo
        self._auth_service = auth_domain_service
        self._password_service = password_service

    async def execute(self, dto: RegisterUserDTO) -> UserResponseDTO:
        if await self._auth_service.email_is_taken(dto.email):
            raise ValueError(f"Email '{dto.email}' is already registered")

        hashed = self._password_service.hash(dto.password)
        user = User(
            email=dto.email,
            hashed_password=hashed,
            full_name=dto.full_name,
            role=dto.role,
        )
        saved = await self._user_repo.save(user)
        return UserResponseDTO(
            id=saved.id,
            email=saved.email,
            full_name=saved.full_name,
            status=saved.status,
            is_superuser=saved.is_superuser,
            role=saved.role,
            created_at=saved.created_at,
            updated_at=saved.updated_at,
        )
