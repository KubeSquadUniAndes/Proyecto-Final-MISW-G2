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
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def mark_available(self) -> None:
        self.status = RoomStatus.DISPONIBLE
        self.updated_at = datetime.now(timezone.utc)

    def mark_occupied(self) -> None:
        self.status = RoomStatus.OCUPADA
        self.updated_at = datetime.now(timezone.utc)

    def mark_maintenance(self) -> None:
        self.status = RoomStatus.MANTENIMIENTO
        self.updated_at = datetime.now(timezone.utc)

    def is_available(self) -> bool:
        return self.status == RoomStatus.DISPONIBLE
