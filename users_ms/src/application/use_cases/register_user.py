from src.application.dtos.user_dto import RegisterUserDTO, UserResponseDTO
from src.domain.entities.user import User
from src.domain.repositories.user_repository_port import UserRepositoryPort
from src.domain.services.password_service_port import PasswordServicePort
from src.domain.services.user_domain_service import UserDomainService


class RegisterUserUseCase:

    def __init__(
        self,
        user_repository: UserRepositoryPort,
        password_service: PasswordServicePort,
    ) -> None:
        self._repo = user_repository
        self._password_service = password_service
        self._domain_service = UserDomainService(user_repository)

    async def execute(self, dto: RegisterUserDTO) -> UserResponseDTO:
        if await self._domain_service.email_is_taken(dto.email):
            raise ValueError(f"Email '{dto.email}' is already registered")

        hashed_password = self._password_service.hash(dto.password)

        user = User(
            first_name=dto.first_name,
            last_name=dto.last_name,
            email=dto.email,
            phone=dto.phone,
            country=dto.country,
            city=dto.city,
            birth_date=dto.birth_date,
            hashed_password=hashed_password,
            user_type=dto.user_type,
            identification_type=dto.identification_type,
            identification_number=dto.identification_number,
        )

        saved = await self._repo.save(user)

        return UserResponseDTO(
            id=saved.id,
            first_name=saved.first_name,
            last_name=saved.last_name,
            email=saved.email,
            phone=saved.phone,
            country=saved.country,
            city=saved.city,
            birth_date=saved.birth_date,
            user_type=saved.user_type,
            identification_type=saved.identification_type,
            identification_number=saved.identification_number,
            created_at=saved.created_at,
        )