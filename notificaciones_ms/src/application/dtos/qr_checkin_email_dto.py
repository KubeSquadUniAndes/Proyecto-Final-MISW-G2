from datetime import date

from pydantic import BaseModel


class QrCheckinEmailDTO(BaseModel):
    reservation_code: str
    guest_name: str
    guest_email: str
    property_name: str
    property_address: str
    check_in: date
    check_out: date
    room_type: str
    num_guests: int
    qr_code: str  # base64-encoded PNG


class QrCancelledEmailDTO(BaseModel):
    reservation_code: str
    guest_name: str
    guest_email: str
    property_name: str
    check_in: date
    check_out: date


class QrEmailResultDTO(BaseModel):
    email_sent: bool
    errors: list[str]
