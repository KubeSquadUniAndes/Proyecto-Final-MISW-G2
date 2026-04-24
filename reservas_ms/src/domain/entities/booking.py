from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4


class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


STATUS_DISPLAY = {
    BookingStatus.PENDING: "Pendiente de pago",
    BookingStatus.CONFIRMED: "Confirmada",
    BookingStatus.CANCELLED: "Cancelada",
    BookingStatus.COMPLETED: "Completada",
}


@dataclass
class Booking:
    user_id: UUID
    hotel_id: UUID
    room_id: UUID
    start_time: datetime
    end_time: datetime
    id: UUID = field(default_factory=uuid4)
    status: BookingStatus = BookingStatus.PENDING
    notes: str | None = None
    booking_code: str | None = None
    room_type: str | None = None
    num_guests: int = 1
    additional_guests: list | None = None
    special_requests: str | None = None
    price_per_night: Decimal | None = None
    total_nights: int | None = None
    total_price: Decimal | None = None
    taxes: Decimal | None = None
    final_price: Decimal | None = None
    traveler_name: str | None = None
    traveler_email: str | None = None
    traveler_phone: str | None = None
    traveler_document: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def status_display(self) -> str:
        return STATUS_DISPLAY.get(self.status, self.status.value)

    @property
    def cancellable(self) -> bool:
        return self.status in (BookingStatus.PENDING, BookingStatus.CONFIRMED)

    def confirm(self) -> None:
        if self.status != BookingStatus.PENDING:
            raise ValueError(f"Cannot confirm a booking with status '{self.status}'")
        self.status = BookingStatus.CONFIRMED
        self.updated_at = datetime.utcnow()

    def reject(self) -> None:
        if self.status != BookingStatus.PENDING:
            raise ValueError(f"Cannot reject a booking with status '{self.status}'")
        self.status = BookingStatus.CANCELLED
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
