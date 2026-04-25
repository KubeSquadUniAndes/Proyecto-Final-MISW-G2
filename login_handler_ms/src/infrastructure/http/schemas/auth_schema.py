from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, field_validator

from src.domain.entities.user import UserRole, UserStatus


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None
    role: UserRole | None = None
    user_id: UUID | None = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com",
                "password": "securepass123",
                "full_name": "John Doe",
            }
        }
    }


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    model_config = {
        "json_schema_extra": {
            "example": {"email": "user@example.com", "password": "securepass123"}
        }
    }


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class BlockUserRequest(BaseModel):
    user_id: UUID
    reason: str | None = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "reason": "Anomalous booking pattern detected",
            }
        }
    }


class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str | None
    status: UserStatus
    is_superuser: bool
    role: UserRole | None
    created_at: datetime
    updated_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class MessageResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    detail: str
    code: str | None = None
