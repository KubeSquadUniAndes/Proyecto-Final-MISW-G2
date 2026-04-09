from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_validator

from src.domain.entities.booking import BookingStatus


class CreateBookingDTO(BaseModel):
    user_id: UUID
    resource_id: UUID
    start_time: datetime
    end_time: datetime
    notes: str | None = None

    @field_validator("end_time")
    @classmethod
    def end_time_must_be_after_start(cls, v, info):
        if "start_time" in info.data and v <= info.data["start_time"]:
            raise ValueError("end_time must be after start_time")
        return v


class UpdateBookingDTO(BaseModel):
    booking_id: UUID
    user_id: UUID  # used to verify ownership
    start_time: datetime | None = None
    end_time: datetime | None = None
    notes: str | None = None

    @field_validator("end_time")
    @classmethod
    def end_after_start(cls, v, info):
        if (
            v
            and "start_time" in info.data
            and info.data["start_time"]
            and v <= info.data["start_time"]
        ):
            raise ValueError("end_time must be after start_time")
        return v


class BookingResponseDTO(BaseModel):
    id: UUID
    user_id: UUID
    resource_id: UUID
    start_time: datetime
    end_time: datetime
    status: BookingStatus
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
