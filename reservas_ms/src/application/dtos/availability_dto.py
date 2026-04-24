"""DTOs for availability queries."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_validator

from src.domain.entities.booking import BookingStatus


class AvailabilityQueryDTO(BaseModel):
    resource_id: UUID
    start_time: datetime
    end_time: datetime
    room_type: str | None = None
    status: BookingStatus | None = None

    @field_validator("end_time")
    @classmethod
    def end_time_must_be_after_start(cls, v, info):
        if "start_time" in info.data and v <= info.data["start_time"]:
            raise ValueError("end_time must be after start_time")
        return v


class BookingSummaryDTO(BaseModel):
    id: UUID
    start_time: datetime
    end_time: datetime
    status: BookingStatus
    status_display: str
    room_type: str | None
    num_guests: int
    booking_code: str | None
    traveler_name: str | None


class AvailabilityResponseDTO(BaseModel):
    resource_id: UUID
    query_range: dict
    filters: dict
    bookings: list[BookingSummaryDTO]
    total_bookings: int
    summary: dict

    model_config = {"from_attributes": True}
