import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.reservation import ReservationStatus


class ReservationCreate(BaseModel):
    traveler_name: str = Field(..., min_length=1, max_length=255)
    traveler_email: EmailStr
    traveler_phone: str = Field(..., pattern=r"^\+?[\d\s\-]{7,20}$")
    traveler_document: str = Field(..., min_length=1, max_length=50)
    destination: str = Field(..., min_length=1, max_length=255)
    origin: str = Field(..., min_length=1, max_length=255)
    departure_date: date
    return_date: Optional[date] = None
    num_passengers: int = Field(..., ge=1, le=50)


class ReservationUpdate(BaseModel):
    traveler_name: Optional[str] = Field(None, min_length=1, max_length=255)
    traveler_email: Optional[EmailStr] = None
    traveler_phone: Optional[str] = Field(None, pattern=r"^\+?[\d\s\-]{7,20}$")
    traveler_document: Optional[str] = Field(None, min_length=1, max_length=50)
    destination: Optional[str] = Field(None, min_length=1, max_length=255)
    origin: Optional[str] = Field(None, min_length=1, max_length=255)
    departure_date: Optional[date] = None
    return_date: Optional[date] = None
    status: Optional[ReservationStatus] = None
    num_passengers: Optional[int] = Field(None, ge=1, le=50)


class ReservationResponse(BaseModel):
    id: uuid.UUID
    traveler_name: str
    traveler_email: str
    traveler_phone: str
    traveler_document: str
    destination: str
    origin: str
    departure_date: date
    return_date: Optional[date]
    status: ReservationStatus
    num_passengers: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReservationListResponse(BaseModel):
    items: list[ReservationResponse]
    total: int
