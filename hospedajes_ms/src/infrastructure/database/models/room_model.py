import uuid

from sqlalchemy import (
    ARRAY,
    Column,
    DateTime,
    Enum,
    Float,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from src.domain.entities.room import RoomStatus, RoomType
from src.infrastructure.database.base import Base


class RoomModel(Base):
    __tablename__ = "rooms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hotel_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    hotel_name = Column(String(255), nullable=True)
    destination = Column(String(255), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    room_type = Column(
        Enum(
            RoomType,
            name="room_type_enum",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )
    price = Column(Numeric(10, 2), nullable=False)
    capacity = Column(Integer, nullable=False)
    beds = Column(Text, nullable=False)
    size = Column(Float, nullable=False)
    status = Column(
        Enum(
            RoomStatus,
            name="room_status_enum",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=RoomStatus.DISPONIBLE,
    )
    amenities = Column(Text, nullable=True)
    # PostgreSQL text[] — stores booking UUID strings that reference this room
    booking_ids = Column(ARRAY(String), nullable=False, server_default="{}")
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
        return f"<RoomModel name={self.name} status={self.status}>"
