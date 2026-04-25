import uuid

from sqlalchemy import Column, DateTime, Enum, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from src.domain.entities.rate import SeasonType
from src.domain.entities.room import RoomType
from src.infrastructure.database.base import Base


class RateModel(Base):
    __tablename__ = "rates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hotel_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    room_type = Column(
        Enum(RoomType, name="rate_room_type_enum", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    season = Column(
        Enum(SeasonType, name="season_type_enum", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    base_price = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<RateModel hotel_id={self.hotel_id} room_type={self.room_type} season={self.season}>"
