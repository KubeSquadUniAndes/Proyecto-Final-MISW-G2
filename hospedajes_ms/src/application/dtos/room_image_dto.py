from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class RoomImageResponseDTO:
    id: UUID
    room_id: UUID
    url: str
    created_at: datetime
