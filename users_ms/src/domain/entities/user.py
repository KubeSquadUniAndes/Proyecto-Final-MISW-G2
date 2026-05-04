from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from uuid import UUID, uuid4


class UserType(str, Enum):
    TRAVELER = "traveler"
    HOTEL = "hotel"


class IdentificationType(str, Enum):
    NIT = "NIT"
    CC = "CC"
    CE = "CE"


@dataclass
class User:
    first_name: str
    last_name: str
    email: str
    phone: str
    country: str
    city: str
    birth_date: date
    hashed_password: str
    user_type: UserType
    identification_type: IdentificationType
    identification_number: str
    id: UUID = field(default_factory=uuid4)
    fcm_token: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def is_hotel(self) -> bool:
        return self.user_type == UserType.HOTEL

    def is_traveler(self) -> bool:
        return self.user_type == UserType.TRAVELER