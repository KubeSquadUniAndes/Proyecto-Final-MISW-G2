from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class HotelImageResponse(BaseModel):
    id: UUID
    hotel_id: UUID
    url: str
    created_at: datetime
