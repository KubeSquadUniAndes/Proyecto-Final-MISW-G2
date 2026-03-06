from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class SendNotificationRequest(BaseModel):
    user_id: UUID
    booking_id: UUID
    anomaly_type: str
    severity: str
    score: float
    description: str
    detected_at: datetime

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "booking_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                "anomaly_type": "random_sample",
                "severity": "medium",
                "score": 0.73,
                "description": "Random sampling triggered anomaly flag (rate=30%)",
                "detected_at": "2026-04-01T10:00:00",
            }
        }
    }


class NotificationResultResponse(BaseModel):
    email_sent: bool
    slack_sent: bool
    errors: list[str]


class ErrorResponse(BaseModel):
    detail: str
