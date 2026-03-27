from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_validator

from src.domain.entities.anomaly_event import AnomalyType, AnomalySeverity


class AnalyzeBookingRequest(BaseModel):
    user_id: UUID
    booking_id: UUID
    resource_id: UUID
    start_time: datetime
    end_time: datetime

    @field_validator("end_time")
    @classmethod
    def end_after_start(cls, v, info):
        if "start_time" in info.data and v <= info.data["start_time"]:
            raise ValueError("end_time must be after start_time")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "booking_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                "resource_id": "987fcdeb-51a2-43f7-b234-426614174111",
                "start_time": "2026-04-01T10:00:00",
                "end_time": "2026-04-01T12:00:00",
            }
        }
    }


class AnomalyEventResponse(BaseModel):
    id: UUID
    user_id: UUID
    booking_id: UUID
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    score: float
    description: str
    created_at: datetime


class AnalysisResultResponse(BaseModel):
    booking_id: UUID
    is_anomalous: bool
    anomaly_count: int
    events: list[AnomalyEventResponse]
    action_taken: str
    message: str


class ErrorResponse(BaseModel):
    detail: str
    code: str | None = None
