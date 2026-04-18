from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from src.domain.entities.room import RoomStatus, RoomType


class CreateRoomDTO(BaseModel):
    name: str
    room_type: RoomType
    price: Decimal
    capacity: int
    beds: str
    size: float
    status: RoomStatus = RoomStatus.DISPONIBLE
    amenities: str


class UpdateRoomDTO(BaseModel):
    name: str | None = None
    room_type: RoomType | None = None
    price: Decimal | None = None
    capacity: int | None = None
    beds: str | None = None
    size: float | None = None
    status: RoomStatus | None = None
    amenities: str | None = None


class RoomResponseDTO(BaseModel):
    id: UUID
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

    model_config = {"from_attributes": True}


class RoomStatsDTO(BaseModel):
    total: int
    disponibles: int
    ocupadas: int
    mantenimiento: int
