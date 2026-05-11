from datetime import date

from pydantic import BaseModel


class ReservationConfirmationRequest(BaseModel):
    reservation_code: str
    guest_name: str
    guest_email: str
    property_name: str
    property_address: str
    check_in: date
    check_out: date
    num_guests: int
    total_amount: float
    property_contact: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "reservation_code": "TH-2026-ABC123",
                "guest_name": "Juan Pérez",
                "guest_email": "juan@example.com",
                "property_name": "Hotel Bogotá Plaza",
                "property_address": "Calle 123 # 45-67, Bogotá",
                "check_in": "2026-06-01",
                "check_out": "2026-06-05",
                "num_guests": 2,
                "total_amount": 850000.00,
                "property_contact": "+57 1 234 5678",
            }
        }
    }


class ReservationConfirmationResponse(BaseModel):
    email_sent: bool
    errors: list[str]
