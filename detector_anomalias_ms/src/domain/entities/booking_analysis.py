from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class BookingAnalysisRequest:
    """Represents an incoming booking that needs anomaly analysis."""
    user_id: UUID
    booking_id: UUID
    resource_id: UUID
    start_time: datetime
    end_time: datetime
    requested_at: datetime = None

    def __post_init__(self):
        if self.requested_at is None:
            self.requested_at = datetime.utcnow()

    @property
    def duration_minutes(self) -> float:
        return (self.end_time - self.start_time).total_seconds() / 60
