from datetime import date
from uuid import UUID

from pydantic import BaseModel


class ReservationConfirmationDTO(BaseModel):
    reservation_code: UUID
    guest_name: str
    guest_email: str
    property_name: str
    property_address: str
    check_in: date
    check_out: date
    num_guests: int
    total_amount: float
    property_contact: str


class ReservationConfirmationResultDTO(BaseModel):
    email_sent: bool
    errors: list[str]
