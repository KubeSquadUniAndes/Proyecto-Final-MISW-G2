from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, field_validator, model_validator

from src.domain.entities.rate import DiscountType, SeasonType
from src.domain.entities.room import RoomType


class CreateRateRequest(BaseModel):
    room_type: RoomType
    season: SeasonType
    base_price: Decimal

    @field_validator("base_price")
    @classmethod
    def base_price_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("base_price must be positive")
        return v


class UpdateRateRequest(BaseModel):
    base_price: Decimal

    @field_validator("base_price")
    @classmethod
    def base_price_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("base_price must be positive")
        return v


class CreateDiscountRequest(BaseModel):
    name: str
    discount_type: DiscountType
    value: Decimal
    start_date: date
    end_date: date

    @field_validator("value")
    @classmethod
    def value_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("value must be positive")
        return v

    @model_validator(mode="after")
    def dates_valid(self) -> "CreateDiscountRequest":
        if self.start_date > self.end_date:
            raise ValueError("start_date must be before or equal to end_date")
        return self


class UpdateDiscountRequest(BaseModel):
    name: str | None = None
    discount_type: DiscountType | None = None
    value: Decimal | None = None
    start_date: date | None = None
    end_date: date | None = None

    @field_validator("value")
    @classmethod
    def value_positive(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and v <= 0:
            raise ValueError("value must be positive")
        return v


class DiscountResponse(BaseModel):
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

    model_config = {"from_attributes": True}


class RateResponse(BaseModel):
    id: UUID
    hotel_id: UUID
    room_type: RoomType
    season: SeasonType
    base_price: Decimal
    final_price: Decimal
    active_discount: DiscountResponse | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EffectivePriceResponse(BaseModel):
    room_type: RoomType
    season: SeasonType | None
    base_price: Decimal
    final_price: Decimal
    has_discount: bool
    discount_name: str | None = None
