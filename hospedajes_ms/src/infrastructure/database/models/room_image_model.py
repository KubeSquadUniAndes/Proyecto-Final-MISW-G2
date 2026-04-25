import uuid

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from src.infrastructure.database.base import Base


class RoomImageModel(Base):
    __tablename__ = "room_images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    url = Column(String(1024), nullable=False)
    s3_key = Column(String(1024), nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<RoomImageModel room_id={self.room_id} id={self.id}>"
