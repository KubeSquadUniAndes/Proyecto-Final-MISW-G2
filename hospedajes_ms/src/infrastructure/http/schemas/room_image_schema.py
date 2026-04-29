from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class RoomImageResponse(BaseModel):
    id: UUID
    room_id: UUID
    url: str
    created_at: datetime
