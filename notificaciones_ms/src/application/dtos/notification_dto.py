from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class SendNotificationDTO(BaseModel):
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


class NotificationResultDTO(BaseModel):
    email_sent: bool
    slack_sent: bool
    errors: list[str]


class BookingNotificationDTO(BaseModel):
    """DTO for booking push notifications via FCM."""

    fcm_token: str
    booking_id: str
    booking_code: str
    hotel_name: str
    check_in: str
    check_out: str
    status: str
    event_type: str  # "created" | "status_changed" | "modified"
    change_summary: str | None = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "fcm_token": "device-fcm-token",
                "booking_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                "booking_code": "TH-2026-ABCDE",
                "hotel_name": "Hotel Cartagena",
                "check_in": "2026-06-01",
                "check_out": "2026-06-05",
                "status": "Pendiente de pago",
                "event_type": "created",
                "change_summary": None,
            }
        }
    }


class BookingNotificationResultDTO(BaseModel):
    fcm_sent: bool
    errors: list[str]
