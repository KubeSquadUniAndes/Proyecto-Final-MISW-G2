from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


@dataclass
class Booking:
    user_id: UUID
    resource_id: UUID
    start_time: datetime
    end_time: datetime
    id: UUID = field(default_factory=uuid4)
    status: BookingStatus = BookingStatus.PENDING
    notes: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def confirm(self) -> None:
        if self.status != BookingStatus.PENDING:
            raise ValueError(f"Cannot confirm a booking with status '{self.status}'")
        self.status = BookingStatus.CONFIRMED
        self.updated_at = datetime.utcnow()

    def cancel(self) -> None:
        if self.status in (BookingStatus.CANCELLED, BookingStatus.COMPLETED):
            raise ValueError(f"Cannot cancel a booking with status '{self.status}'")
        self.status = BookingStatus.CANCELLED
        self.updated_at = datetime.utcnow()

    def complete(self) -> None:
        if self.status != BookingStatus.CONFIRMED:
            raise ValueError(f"Cannot complete a booking with status '{self.status}'")
        self.status = BookingStatus.COMPLETED
        self.updated_at = datetime.utcnow()

    def is_valid(self) -> bool:
        return self.start_time < self.end_time
