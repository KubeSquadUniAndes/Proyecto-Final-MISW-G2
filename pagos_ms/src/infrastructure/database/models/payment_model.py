import uuid

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Integer,
    LargeBinary,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from src.infrastructure.database.base import Base
from src.domain.entities.payment import PaymentStatus, PaymentProvider, PaymentMethod


class PaymentModel(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id = Column(UUID(as_uuid=True), nullable=False, index=True, unique=True)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    payment_provider = Column(
        Enum(PaymentProvider, name="payment_provider_enum"), nullable=False
    )
    payment_method = Column(
        Enum(PaymentMethod, name="payment_method_enum"), nullable=False
    )
    status = Column(
        Enum(PaymentStatus, name="payment_status_enum"),
        nullable=False,
        default=PaymentStatus.PENDING,
    )
    provider_transaction_id = Column(String(255), nullable=True, index=True)
    card_last_four = Column(String(4), nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    payment_timestamp = Column(DateTime(timezone=True), nullable=True)

    # Sensitive fields — encrypted with pgcrypto AES-256
    cardholder_name = Column(LargeBinary, nullable=True)
    cardholder_email = Column(LargeBinary, nullable=True)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<PaymentModel id={self.id} status={self.status}>"
