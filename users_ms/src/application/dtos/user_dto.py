from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from src.domain.entities.user import IdentificationType, UserType


class RegisterUserDTO(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100, examples=["Juan"])
    last_name: str = Field(..., min_length=1, max_length=100, examples=["Pérez"])
    email: EmailStr = Field(..., examples=["juan@example.com"])
    phone: str = Field(..., min_length=7, max_length=20, examples=["+57 300 123 4567"])
    country: str = Field(..., min_length=1, max_length=100, examples=["Colombia"])
    city: str = Field(..., min_length=1, max_length=100, examples=["Bogotá"])
    birth_date: date = Field(..., examples=["1995-06-15"])
    password: str = Field(..., min_length=8, max_length=128, examples=["SecurePass123!"])
    user_type: UserType = Field(..., examples=["traveler"])
    identification_type: IdentificationType = Field(..., examples=["CC"])
    identification_number: str = Field(..., min_length=1, max_length=20, examples=["1234567890"])

    @field_validator("birth_date")
    @classmethod
    def birth_date_must_be_in_past(cls, v: date) -> date:
        if v >= date.today():
            raise ValueError("birth_date must be in the past")
        return v

    @field_validator("phone")
    @classmethod
    def phone_must_not_be_empty(cls, v: str) -> str:
        cleaned = v.replace(" ", "").replace("-", "").replace("+", "")
        if not cleaned.isdigit():
            raise ValueError("phone must contain only digits, spaces, hyphens or leading +")
        return v

    @field_validator("identification_number")
    @classmethod
    def identification_number_must_be_valid(cls, v: str) -> str:
        cleaned = v.replace("-", "").replace(".", "")
        if not cleaned.isdigit():
            raise ValueError("identification_number must contain only digits")
        return v


class UserResponseDTO(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    email: str
    phone: str
    country: str
    city: str
    birth_date: date
    user_type: UserType
    identification_type: IdentificationType
    identification_number: str
    created_at: datetime

    model_config = {"from_attributes": True}