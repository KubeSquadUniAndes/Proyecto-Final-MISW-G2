from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from src.domain.entities.anomaly_event import AnomalyType, AnomalySeverity


# ── Request DTOs ─────────────────────────────────────────────────────────────


class AnalyzeBookingDTO(BaseModel):
    user_id: UUID
    booking_id: UUID
    resource_id: UUID
    start_time: datetime
    end_time: datetime


# ── Response DTOs ─────────────────────────────────────────────────────────────


class AnomalyEventDTO(BaseModel):
    id: UUID
    user_id: UUID
    booking_id: UUID
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    score: float
    description: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AnalysisResultDTO(BaseModel):
    booking_id: UUID
    is_anomalous: bool
    anomaly_count: int
    events: list[AnomalyEventDTO]
    action_taken: str  # "none" | "user_blocked" | "alert_sent"
    message: str
