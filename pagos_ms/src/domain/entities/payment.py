import uuid
from datetime import datetime
from enum import Enum
from typing import Optional


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentProvider(str, Enum):
    STRIPE = "stripe"
    PAYPAL = "paypal"
    MERCADOPAGO = "mercadopago"
    MOCK = "mock"


class PaymentMethod(str, Enum):
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    PAYPAL = "paypal"
    BANK_TRANSFER = "bank_transfer"


class Payment:
    def __init__(
        self,
        booking_id: uuid.UUID,
        amount: float,
        currency: str,
        payment_provider: PaymentProvider,
        payment_method: PaymentMethod,
        id: Optional[uuid.UUID] = None,
        status: PaymentStatus = PaymentStatus.PENDING,
        provider_transaction_id: Optional[str] = None,
        card_last_four: Optional[str] = None,
        cardholder_name: Optional[str] = None,
        cardholder_email: Optional[str] = None,
        retry_count: int = 0,
        payment_timestamp: Optional[datetime] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.id = id or uuid.uuid4()
        self.booking_id = booking_id
        self.amount = amount
        self.currency = currency
        self.payment_provider = payment_provider
        self.payment_method = payment_method
        self.status = status
        self.provider_transaction_id = provider_transaction_id
        self.card_last_four = card_last_four
        self.cardholder_name = cardholder_name
        self.cardholder_email = cardholder_email
        self.retry_count = retry_count
        self.payment_timestamp = payment_timestamp
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

    def confirm(self, provider_transaction_id: str, payment_timestamp: datetime):
        self.status = PaymentStatus.CONFIRMED
        self.provider_transaction_id = provider_transaction_id
        self.payment_timestamp = payment_timestamp
        self.updated_at = datetime.utcnow()

    def fail(self):
        self.status = PaymentStatus.FAILED
        self.updated_at = datetime.utcnow()

    def increment_retry(self):
        self.retry_count += 1
        self.updated_at = datetime.utcnow()

    def __repr__(self) -> str:
        return f"<Payment id={self.id} booking_id={self.booking_id} status={self.status}>"
