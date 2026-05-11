from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass
class RoomAvailabilityEvent:
    event_type: str  # "booking_created" | "booking_updated"
    booking_id: UUID
    room_id: UUID
    hotel_id: UUID
    status: str  # booking status value: pending, confirmed, cancelled, completed
    start_time: datetime
    end_time: datetime
    published_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    trace_id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self) -> dict:
        return {
            "trace_id": self.trace_id,
            "event_type": self.event_type,
            "booking_id": str(self.booking_id),
            "room_id": str(self.room_id),
            "hotel_id": str(self.hotel_id),
            "status": self.status,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "published_at": self.published_at.isoformat(),
        }
