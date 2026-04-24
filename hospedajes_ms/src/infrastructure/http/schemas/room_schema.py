from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, field_validator

from src.domain.entities.room import RoomStatus, RoomType


class CreateRoomRequest(BaseModel):
    name: str
    room_type: RoomType
    price: Decimal
    capacity: int
    beds: str
    size: float
    status: RoomStatus = RoomStatus.DISPONIBLE
    amenities: str = ""

    @field_validator("price")
    @classmethod
    def price_non_negative(cls, v: Decimal) -> Decimal:
        if v < Decimal("0"):
            raise ValueError("Price must be non-negative")
        return v

    @field_validator("capacity")
    @classmethod
    def capacity_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Capacity must be at least 1")
        return v

    @field_validator("size")
    @classmethod
    def size_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Size must be positive")
        return v


class UpdateRoomRequest(BaseModel):
    name: str | None = None
    room_type: RoomType | None = None
    price: Decimal | None = None
    capacity: int | None = None
    beds: str | None = None
    size: float | None = None
    status: RoomStatus | None = None
    amenities: str | None = None


class RoomResponse(BaseModel):
    id: UUID
    hotel_id: UUID
    hotel_name: str | None = None
    name: str
    room_type: RoomType
    price: Decimal
    capacity: int
    beds: str
    size: float
    status: RoomStatus
    amenities: str
    created_at: datetime
    updated_at: datetime


class RoomStatsResponse(BaseModel):
    total: int
    disponibles: int
    ocupadas: int
    mantenimiento: int


class MessageResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    detail: str
