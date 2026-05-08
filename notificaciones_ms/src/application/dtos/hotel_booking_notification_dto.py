from datetime import date
from pydantic import BaseModel


class HotelBookingNotificationDTO(BaseModel):
    hotel_email: str
    hotel_name: str
    guest_name: str
    check_in: date
    check_out: date
    num_guests: int
    booking_code: str
    room_type: str
    total_amount: float
    dashboard_url: str = "https://d1iioxb0yhodky.cloudfront.net/booking-requests"


class HotelBookingNotificationResultDTO(BaseModel):
    email_sent: bool
    errors: list[str]
