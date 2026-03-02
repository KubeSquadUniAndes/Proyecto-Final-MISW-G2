import uuid
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Optional


class ReservationStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    MODIFIED = "MODIFIED"


@dataclass
class Reservation:
    id: uuid.UUID
    traveler_name: str
    traveler_email: str
    traveler_phone: str
    traveler_document: str
    destination: str
    origin: str
    departure_date: date
    return_date: Optional[date]
    status: ReservationStatus
    num_passengers: int
    created_at: datetime
    updated_at: datetime
