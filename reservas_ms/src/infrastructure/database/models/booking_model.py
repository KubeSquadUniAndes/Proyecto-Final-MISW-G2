import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    JSON,
    LargeBinary,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from src.infrastructure.database.base import Base
from src.domain.entities.booking import BookingStatus

_BOOKING_STATUS_VALUES = [e.value for e in BookingStatus]


class BookingModel(Base):
    __tablename__ = "bookings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    hotel_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    room_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    # NOTE: String(50) avoids SQLAlchemy's Enum C-extension validator which
    # conflicts with asyncpg's codec cache in Python 3.12.  All writes to this
    # column use raw SQL with an explicit ::booking_status_enum cast; see
    # SQLAlchemyBookingRepository._update_status_raw().
    # server_default uses a SQL literal so PostgreSQL handles the implicit cast
    # to booking_status_enum — bypassing the ::VARCHAR that bound parameters send.
    status = Column(String(50), nullable=False, server_default="'pending'")
    notes = Column(Text, nullable=True)
    # Booking identity
    booking_code = Column(String(15), nullable=True, unique=True, index=True)
    room_type = Column(String(100), nullable=True)
    num_guests = Column(Integer, nullable=True, default=1)
    additional_guests = Column(JSON, nullable=True)
    special_requests = Column(Text, nullable=True)
    # Pricing
    price_per_night = Column(Numeric(10, 2), nullable=True)
    total_nights = Column(Integer, nullable=True)
    total_price = Column(Numeric(10, 2), nullable=True)
    taxes = Column(Numeric(10, 2), nullable=True)
    final_price = Column(Numeric(10, 2), nullable=True)
    # Payment
    payment_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    payment_status = Column(String(50), nullable=True)
    # Sensitive fields — stored as bytea encrypted with pgcrypto AES-256
    traveler_name = Column(LargeBinary, nullable=True)
    traveler_email = Column(LargeBinary, nullable=True)
    traveler_phone = Column(LargeBinary, nullable=True)
    traveler_document = Column(LargeBinary, nullable=True)
    # QR check-in
    qr_code = Column(Text, nullable=True)
    qr_generated_at = Column(DateTime(timezone=True), nullable=True)
    qr_is_valid = Column(Boolean, nullable=False, server_default="true", default=True)
    # Check-in audit (C7)
    checked_in_at = Column(DateTime(timezone=True), nullable=True)
    checkin_staff_id = Column(String(255), nullable=True)
    checkin_device = Column(String(255), nullable=True)
    checkin_ip = Column(String(45), nullable=True)
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
        return f"<BookingModel id={self.id} status={self.status}>"
