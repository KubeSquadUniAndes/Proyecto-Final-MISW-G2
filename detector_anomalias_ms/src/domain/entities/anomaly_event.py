from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class AnomalyType(str, Enum):
    HIGH_FREQUENCY = "high_frequency"  # Too many bookings in a short window
    UNUSUAL_DURATION = "unusual_duration"  # Booking duration outside normal range
    MULTI_RESOURCE = "multi_resource"  # Many different resources in a short window
    RANDOM_SAMPLE = "random_sample"  # Triggered by configurable random sampling


class AnomalySeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class AnomalyEvent:
    user_id: UUID
    booking_id: UUID
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    score: float  # 0.0 – 1.0, higher = more anomalous
    description: str
    id: UUID = field(default_factory=uuid4)
    resolved: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)

    def is_high_risk(self) -> bool:
        return self.severity == AnomalySeverity.HIGH or self.score >= 0.8

    def resolve(self) -> None:
        self.resolved = True
