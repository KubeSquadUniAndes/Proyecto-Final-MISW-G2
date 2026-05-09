from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dtos.auth_dto import (
    BlockUserDTO,
    LoginDTO,
    RefreshTokenDTO,
    RegisterUserDTO,
)
from src.application.use_cases.block_user import BlockUserUseCase
from src.application.use_cases.get_me import GetMeUseCase
from src.application.use_cases.login import LoginUseCase
from src.application.use_cases.logout import LogoutUseCase
from src.application.use_cases.refresh_token import RefreshTokenUseCase
from src.application.use_cases.register_user import RegisterUserUseCase
from src.domain.services.auth_domain_service import AuthDomainService
from src.infrastructure.database.base import get_db
from src.infrastructure.database.repositories.sqlalchemy_refresh_token_repository import (
    SQLAlchemyRefreshTokenRepository,
)
from src.infrastructure.database.repositories.sqlalchemy_user_repository import (
    SQLAlchemyUserRepository,
)
from src.infrastructure.http.dependencies import (
    get_current_user_id,
    require_internal_api_key,
)
from src.infrastructure.http.schemas.auth_schema import (
    BlockUserRequest,
    ErrorResponse,
    LoginRequest,
    MessageResponse,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from src.infrastructure.security.bcrypt_password_service import BcryptPasswordService
from src.infrastructure.security.jwt_service import JWTService

router = APIRouter(prefix="/auth", tags=["Auth"])

# Shared service instances (stateless, safe to reuse)
_jwt_service = JWTService()
_password_service = BcryptPasswordService()


# ── Composition helpers ───────────────────────────────────────────────────────


def _make_repos(db: AsyncSession):
    user_repo = SQLAlchemyUserRepository(db)
    token_repo = SQLAlchemyRefreshTokenRepository(db)
    return user_repo, token_repo


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    responses={409: {"model": ErrorResponse, "description": "Email already taken"}},
)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    user_repo, token_repo = _make_repos(db)
    auth_service = AuthDomainService(user_repo, _password_service)
    use_case = RegisterUserUseCase(user_repo, auth_service, _password_service)
    try:
        result = await use_case.execute(RegisterUserDTO(**body.model_dump()))
        return UserResponse(**result.model_dump())
    except ValueError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc))


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and obtain JWT tokens",
    responses={
        401: {"model": ErrorResponse, "description": "Invalid credentials"},
        403: {"model": ErrorResponse, "description": "Account blocked or inactive"},
    },
)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    user_repo, token_repo = _make_repos(db)
    auth_service = AuthDomainService(user_repo, _password_service)
    use_case = LoginUseCase(auth_service, _jwt_service, token_repo)
    try:
        result = await use_case.execute(LoginDTO(**body.model_dump()))
        return TokenResponse(**result.model_dump())
    except ValueError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=str(exc))


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout and revoke refresh token",
)
async def logout(body: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    _, token_repo = _make_repos(db)
    use_case = LogoutUseCase(token_repo)
    try:
        result = await use_case.execute(RefreshTokenDTO(**body.model_dump()))
        return MessageResponse(**result.model_dump())
    except ValueError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "/refresh-token",
    response_model=TokenResponse,
    summary="Rotate refresh token and get new token pair",
    responses={
        401: {"model": ErrorResponse, "description": "Invalid or expired token"}
    },
)
async def refresh_token(body: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    user_repo, token_repo = _make_repos(db)
    use_case = RefreshTokenUseCase(_jwt_service, token_repo, user_repo)
    try:
        result = await use_case.execute(RefreshTokenDTO(**body.model_dump()))
        return TokenResponse(**result.model_dump())
    except ValueError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=str(exc))


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current authenticated user profile",
)
async def get_me(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    user_repo, _ = _make_repos(db)
    use_case = GetMeUseCase(user_repo)
    try:
        result = await use_case.execute(user_id)
        return UserResponse(**result.model_dump())
    except ValueError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "/block-user",
    response_model=MessageResponse,
    summary="Block a user and revoke all their sessions",
    description=(
        "Called internally by `detector_anomalias_ms` when an anomaly is detected. "
        "Requires the `X-Api-Key` header with the internal API key."
    ),
    responses={403: {"model": ErrorResponse, "description": "Invalid API key"}},
)
async def block_user(
    body: BlockUserRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_internal_api_key),
):
    user_repo, token_repo = _make_repos(db)
    use_case = BlockUserUseCase(user_repo, token_repo)
    try:
        result = await use_case.execute(BlockUserDTO(**body.model_dump()))
        return MessageResponse(**result.model_dump())
    except ValueError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get(
    "/users/{user_id}/email",
    summary="Get user email by ID (internal)",
    responses={404: {"model": ErrorResponse}},
)
async def get_user_email(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_internal_api_key),
):
    user_repo, _ = _make_repos(db)
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"email": user.email, "full_name": user.full_name}
