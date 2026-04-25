import uuid

from sqlalchemy import Column, Date, DateTime, Enum, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from src.domain.entities.rate import DiscountType
from src.infrastructure.database.base import Base


class DiscountModel(Base):
    __tablename__ = "discounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rate_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    discount_type = Column(
        Enum(
            DiscountType,
            name="discount_type_enum",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )
    value = Column(Numeric(10, 2), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
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
        return f"<DiscountModel name={self.name} rate_id={self.rate_id}>"
