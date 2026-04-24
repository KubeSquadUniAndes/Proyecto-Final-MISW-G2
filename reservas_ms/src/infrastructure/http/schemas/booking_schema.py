from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, field_validator

from src.domain.entities.booking import BookingStatus


class CreateBookingRequest(BaseModel):
    resource_id: UUID
    start_time: datetime
    end_time: datetime
    notes: str | None = None
    room_type: str | None = None
    num_guests: int = 1
    additional_guests: list | None = None
    special_requests: str | None = None
    price_per_night: Decimal | None = None
    traveler_name: str | None = None
    traveler_email: str | None = None
    traveler_phone: str | None = None
    traveler_document: str | None = None

    @field_validator("end_time")
    @classmethod
    def end_time_must_be_after_start(cls, v, info):
        if "start_time" in info.data and v <= info.data["start_time"]:
            raise ValueError("end_time must be after start_time")
        return v


class UpdateBookingRequest(BaseModel):
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


class BookingResponse(BaseModel):
    id: UUID
    user_id: UUID
    resource_id: UUID
    start_time: datetime
    end_time: datetime
    status: BookingStatus
    status_display: str
    notes: str | None
    booking_code: str | None
    room_type: str | None
    num_guests: int
    additional_guests: list | None
    special_requests: str | None
    price_per_night: Decimal | None
    total_nights: int | None
    total_price: Decimal | None
    taxes: Decimal | None
    final_price: Decimal | None
    traveler_name: str | None
    traveler_email: str | None
    traveler_phone: str | None
    traveler_document: str | None
    cancellable: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ErrorResponse(BaseModel):
    detail: str
    code: str | None = None


class RejectBookingRequest(BaseModel):
    rejection_reason: str


class AvailabilityResponse(BaseModel):
    resource_id: UUID
    query_range: dict
    filters: dict
    bookings: list[dict]
    total_bookings: int
    summary: dict
