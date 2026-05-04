from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dtos.user_dto import RegisterUserDTO, UserResponseDTO
from src.application.use_cases.register_user import RegisterUserUseCase
from src.infrastructure.clients.login_handler_client import LoginHandlerClient
from src.infrastructure.config.settings import settings
from src.infrastructure.database.database import get_db
from src.infrastructure.database.repositories.sqlalchemy_user_repository import (
    SQLAlchemyUserRepository,
)
from src.infrastructure.security.bcrypt_password_service import BcryptPasswordService

router = APIRouter(prefix="/api/v1/users", tags=["users"])


class FcmTokenRequest(BaseModel):
    fcm_token: str
    platform: str = "android"


def get_register_use_case(db: AsyncSession = Depends(get_db)) -> RegisterUserUseCase:
    repo = SQLAlchemyUserRepository(db)
    password_service = BcryptPasswordService()
    login_handler_client = LoginHandlerClient()
    return RegisterUserUseCase(
        user_repository=repo,
        password_service=password_service,
        login_handler_client=login_handler_client,
    )


@router.get(
    "/{user_id}",
    response_model=UserResponseDTO,
    summary="Get user by ID (internal)",
)
async def get_user_by_id(
    user_id: UUID,
    x_internal_api_key: str = Header(..., alias="X-Internal-Api-Key"),
    db: AsyncSession = Depends(get_db),
) -> UserResponseDTO:
    if x_internal_api_key != settings.INTERNAL_API_KEY:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid internal API key")
    repo = SQLAlchemyUserRepository(db)
    user = await repo.find_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponseDTO.model_validate(user)


@router.post(
    "/register",
    response_model=UserResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Creates a new user account and registers credentials in login_handler_ms.",
)
async def register_user(
    dto: RegisterUserDTO,
    use_case: RegisterUserUseCase = Depends(get_register_use_case),
) -> UserResponseDTO:
    try:
        return await use_case.execute(dto)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )


@router.post(
    "/fcm-token",
    status_code=status.HTTP_200_OK,
    summary="Register or update FCM token for push notifications",
)
async def register_fcm_token(
    body: FcmTokenRequest,
    authorization: str = Header(..., alias="Authorization"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    import jwt
    try:
        token = authorization.removeprefix("Bearer ").strip()
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id = UUID(payload["sub"])
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    repo = SQLAlchemyUserRepository(db)
    updated = await repo.update_fcm_token(user_id, body.fcm_token)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"message": "FCM token registered successfully"}


@router.get(
    "/{user_id}/fcm-token",
    status_code=status.HTTP_200_OK,
    summary="Get FCM token for a user (internal)",
)
async def get_fcm_token(
    user_id: UUID,
    x_internal_api_key: str = Header(..., alias="X-Internal-Api-Key"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if x_internal_api_key != settings.INTERNAL_API_KEY:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid internal API key")
    repo = SQLAlchemyUserRepository(db)
    token = await repo.get_fcm_token(user_id)
    return {"fcm_token": token}
