from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr

from src.domain.entities.user import UserRole, UserStatus


# ── Request DTOs ─────────────────────────────────────────────────────────────

class RegisterUserDTO(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None
    role: UserRole | None = None


class LoginDTO(BaseModel):
    email: EmailStr
    password: str


class RefreshTokenDTO(BaseModel):
    refresh_token: str


class BlockUserDTO(BaseModel):
    user_id: UUID
    reason: str | None = None


# ── Response DTOs ─────────────────────────────────────────────────────────────

class UserResponseDTO(BaseModel):
    id: UUID
    email: str
    full_name: str | None
    status: UserStatus
    is_superuser: bool
    role: UserRole | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TokenResponseDTO(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class MessageDTO(BaseModel):
    message: str
