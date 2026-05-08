from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from src.domain.entities.payment import PaymentStatus, PaymentProvider, PaymentMethod


class CreatePaymentRequest(BaseModel):
    booking_id: UUID
    amount: float = Field(gt=0)
    currency: str = Field(default="USD", max_length=3)
    payment_provider: PaymentProvider
    payment_method: PaymentMethod
    card_last_four: Optional[str] = Field(None, max_length=4)
    cardholder_name: Optional[str] = None
    cardholder_email: Optional[str] = None


class ConfirmPaymentRequest(BaseModel):
    provider_transaction_id: str
    payment_timestamp: Optional[datetime] = None


class PaymentResponse(BaseModel):
    id: UUID
    booking_id: UUID
    amount: float
    currency: str
    payment_provider: PaymentProvider
    payment_method: PaymentMethod
    status: PaymentStatus
    provider_transaction_id: Optional[str] = None
    card_last_four: Optional[str] = None
    retry_count: int
    payment_timestamp: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
