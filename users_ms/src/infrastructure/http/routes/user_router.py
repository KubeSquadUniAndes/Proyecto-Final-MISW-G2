from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dtos.user_dto import RegisterUserDTO, UserResponseDTO
from src.application.use_cases.register_user import RegisterUserUseCase
from src.infrastructure.database.database import get_db
from src.infrastructure.database.repositories.sqlalchemy_user_repository import (
    SQLAlchemyUserRepository,
)
from src.infrastructure.security.bcrypt_password_service import BcryptPasswordService

router = APIRouter(prefix="/api/v1/users", tags=["users"])


def get_register_use_case(db: AsyncSession = Depends(get_db)) -> RegisterUserUseCase:
    repo = SQLAlchemyUserRepository(db)
    password_service = BcryptPasswordService()
    return RegisterUserUseCase(user_repository=repo, password_service=password_service)


@router.post(
    "/register",
    response_model=UserResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Creates a new user account with personal information.",
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
