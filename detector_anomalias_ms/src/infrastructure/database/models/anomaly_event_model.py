import uuid

from sqlalchemy import Column, Boolean, DateTime, Enum, Float, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from src.infrastructure.database.base import Base
from src.domain.entities.anomaly_event import AnomalyType, AnomalySeverity


class AnomalyEventModel(Base):
    __tablename__ = "anomaly_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    booking_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    anomaly_type = Column(Enum(AnomalyType, name="anomaly_type_enum"), nullable=False)
    severity = Column(
        Enum(AnomalySeverity, name="anomaly_severity_enum"), nullable=False
    )
    score = Column(Float, nullable=False)
    description = Column(Text, nullable=False)
    resolved = Column(Boolean, nullable=False, default=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<AnomalyEventModel type={self.anomaly_type} severity={self.severity} score={self.score}>"
