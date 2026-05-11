from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4


class RoomType(str, Enum):
    INDIVIDUAL = "individual"
    DOBLE = "doble"
    SUITE = "suite"


class RoomStatus(str, Enum):
    DISPONIBLE = "disponible"
    PARCIAL = "parcial"       # has at least one active booking in any date range
    OCUPADA = "ocupada"
    MANTENIMIENTO = "mantenimiento"


@dataclass
class Room:
    name: str
    room_type: RoomType
    price: Decimal
    capacity: int
    beds: str
    size: float
    status: RoomStatus
    amenities: str
    hotel_id: UUID = field(default_factory=uuid4)
    hotel_name: str | None = None
    destination: str | None = None
    id: UUID = field(default_factory=uuid4)
    # UUIDs (as strings) of bookings that reference this room
    booking_ids: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # ── Booking-ID management ─────────────────────────────────────────────────

    def add_booking(self, booking_id: str) -> None:
        """Register a booking against this room and recompute status."""
        if booking_id not in self.booking_ids:
            self.booking_ids.append(booking_id)
        self._recompute_status()

    def remove_booking(self, booking_id: str) -> None:
        """Release a booking from this room and recompute status."""
        self.booking_ids = [b for b in self.booking_ids if b != booking_id]
        self._recompute_status()

    def _recompute_status(self) -> None:
        """Derive status from booking_ids. Does NOT override MANTENIMIENTO."""
        if self.status == RoomStatus.MANTENIMIENTO:
            return
        self.status = RoomStatus.PARCIAL if self.booking_ids else RoomStatus.DISPONIBLE
        self.updated_at = datetime.now(timezone.utc)

    # ── Manual status helpers ─────────────────────────────────────────────────

    def mark_occupied(self) -> None:
        self.status = RoomStatus.OCUPADA
        self.updated_at = datetime.now(timezone.utc)

    def mark_maintenance(self) -> None:
        self.status = RoomStatus.MANTENIMIENTO
        self.updated_at = datetime.now(timezone.utc)

    def is_available(self) -> bool:
        return self.status == RoomStatus.DISPONIBLE
