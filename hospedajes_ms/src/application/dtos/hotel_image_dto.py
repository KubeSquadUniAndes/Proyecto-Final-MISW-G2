from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class HotelImageResponseDTO:
    id: UUID
    hotel_id: UUID
    url: str
    created_at: datetime
