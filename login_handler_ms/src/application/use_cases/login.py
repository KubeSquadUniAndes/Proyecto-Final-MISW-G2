from src.application.dtos.auth_dto import LoginDTO, TokenResponseDTO
from src.application.dtos.jwt_service_port import JWTServicePort
from src.domain.entities.refresh_token import RefreshToken
from src.domain.repositories.refresh_token_repository_port import (
    RefreshTokenRepositoryPort,
)
from src.domain.services.auth_domain_service import AuthDomainService


class LoginUseCase:
    """Input port: authenticates a user and issues JWT tokens."""

    def __init__(
        self,
        auth_domain_service: AuthDomainService,
        jwt_service: JWTServicePort,
        refresh_token_repo: RefreshTokenRepositoryPort,
    ) -> None:
        self._auth_service = auth_domain_service
        self._jwt = jwt_service
        self._refresh_repo = refresh_token_repo

    async def execute(self, dto: LoginDTO) -> TokenResponseDTO:
        user = await self._auth_service.authenticate(dto.email, dto.password)
        if not user:
            raise ValueError("Invalid email or password")
        if user.is_blocked():
            raise PermissionError("User account is blocked")
        if not user.is_active():
            raise PermissionError("User account is inactive")

        extra_claims = {"role": user.role.value} if user.role else {}
        access_token = self._jwt.create_access_token(user.id, extra_claims=extra_claims)
        raw_refresh, expires_at = self._jwt.create_refresh_token(user.id)

        token_entity = RefreshToken(
            user_id=user.id,
            token=raw_refresh,
            expires_at=expires_at,
        )
        await self._refresh_repo.save(token_entity)

        return TokenResponseDTO(
            access_token=access_token,
            refresh_token=raw_refresh,
        )
