from datetime import date, datetime

from pydantic import BaseModel


class PaymentVoucherRequest(BaseModel):
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
    payment_method: str

    nightly_rate: float
    num_nights: int
    subtotal: float
    taxes: float
    discounts: float
    total_amount: float

    model_config = {
        "json_schema_extra": {
            "example": {
                "guest_name": "Juan Pérez",
                "guest_email": "juan@example.com",
                "reservation_code": "TH-2026-00123",
                "property_name": "Hotel Bogotá Plaza",
                "property_address": "Calle 123 # 45-67, Bogotá",
                "check_in": "2026-06-01",
                "check_out": "2026-06-05",
                "room_type": "Habitación Doble Estándar",
                "num_guests": 2,
                "transaction_id": "txn_3PqK2aLkdIwHu7ix0J4M5N6O",
                "paid_at": "2026-05-09T14:32:10",
                "payment_method": "Visa •••• 4242",
                "nightly_rate": 200000.00,
                "num_nights": 4,
                "subtotal": 800000.00,
                "taxes": 152000.00,
                "discounts": 0.00,
                "total_amount": 952000.00,
            }
        }
    }


class PaymentVoucherResponse(BaseModel):
    email_sent: bool
    errors: list[str]
