from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

from src.domain.entities.room import RoomType


class SeasonType(str, Enum):
    BASE = "base"
    ALTA = "alta"
    MEDIA = "media"
    BAJA = "baja"


class DiscountType(str, Enum):
    PORCENTAJE = "porcentaje"
    FIJO = "fijo"


@dataclass
class Discount:
    rate_id: UUID
    name: str
    discount_type: DiscountType
    value: Decimal
    start_date: date
    end_date: date
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def is_active(self) -> bool:
        today = date.today()
        return self.start_date <= today <= self.end_date

    def apply(self, base_price: Decimal) -> Decimal:
        if self.discount_type == DiscountType.PORCENTAJE:
            return base_price * (1 - self.value / Decimal("100"))
        return base_price - self.value


@dataclass
class Rate:
    hotel_id: UUID
    room_type: RoomType
    season: SeasonType
    base_price: Decimal
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def effective_price(
        self, discounts: list[Discount]
    ) -> tuple[Decimal, "Discount | None"]:
        active = next((d for d in discounts if d.is_active()), None)
        if active:
            return active.apply(self.base_price), active
        return self.base_price, None
