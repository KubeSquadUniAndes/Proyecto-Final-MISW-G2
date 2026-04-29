from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from src.domain.entities.rate import DiscountType, SeasonType
from src.domain.entities.room import RoomType


@dataclass
class CreateRateDTO:
    hotel_id: UUID
    room_type: RoomType
    season: SeasonType
    base_price: Decimal


@dataclass
class UpdateRateDTO:
    base_price: Decimal


@dataclass
class CreateDiscountDTO:
    rate_id: UUID
    name: str
    discount_type: DiscountType
    value: Decimal
    start_date: date
    end_date: date


@dataclass
class UpdateDiscountDTO:
    name: str | None = None
    discount_type: DiscountType | None = None
    value: Decimal | None = None
    start_date: date | None = None
    end_date: date | None = None


@dataclass
class DiscountResponseDTO:
    id: UUID
    rate_id: UUID
    name: str
    discount_type: DiscountType
    value: Decimal
    start_date: date
    end_date: date
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass
class RateResponseDTO:
    id: UUID
    hotel_id: UUID
    room_type: RoomType
    season: SeasonType
    base_price: Decimal
    final_price: Decimal
    active_discount: DiscountResponseDTO | None
    created_at: datetime
    updated_at: datetime
