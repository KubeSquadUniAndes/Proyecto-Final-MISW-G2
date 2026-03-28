from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_validator

from src.domain.entities.booking import BookingStatus


class CreateBookingRequest(BaseModel):
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

    model_config = {
        "json_schema_extra": {
            "example": {
                "resource_id": "987fcdeb-51a2-43f7-b234-426614174111",
                "start_time": "2026-04-01T10:00:00",
                "end_time": "2026-04-01T12:00:00",
                "notes": "Q2 team meeting",
            }
        }
    }


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

    model_config = {
        "json_schema_extra": {
            "example": {
                "start_time": "2026-04-01T11:00:00",
                "end_time": "2026-04-01T13:00:00",
                "notes": "Updated notes",
            }
        }
    }


class BookingResponse(BaseModel):
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


class ErrorResponse(BaseModel):
    detail: str
    code: str | None = None
