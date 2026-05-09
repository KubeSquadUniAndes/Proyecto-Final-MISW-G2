from datetime import date, datetime

from pydantic import BaseModel


class PaymentVoucherDTO(BaseModel):
    guest_name: str
    guest_email: str

    reservation_code: str
    property_name: str
    property_address: str
    check_in: date
    check_out: date
    room_type: str
    num_guests: int

    transaction_id: str
    paid_at: datetime
    payment_method: str  # e.g. "Visa •••• 4242"

    nightly_rate: float
    num_nights: int
    subtotal: float
    taxes: float
    discounts: float
    total_amount: float


class PaymentVoucherResultDTO(BaseModel):
    email_sent: bool
    errors: list[str]
