"""Unit tests for ListBookingsByHotelUseCase."""

from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from src.application.use_cases.list_bookings_by_hotel import ListBookingsByHotelUseCase
from src.domain.entities.booking import Booking, BookingStatus


class MockBookingRepository:
    def __init__(self):
        self.bookings = []

    async def list_by_hotel(self, hotel_id):
        return [b for b in self.bookings if b.hotel_id == hotel_id]


@pytest.mark.asyncio
async def test_list_bookings_by_hotel_success():
    """Test listing bookings for a hotel."""
    repo = MockBookingRepository()
    use_case = ListBookingsByHotelUseCase(repo)

    hotel_id = uuid4()
    booking1 = Booking(
        id=uuid4(),
        user_id=uuid4(),
        hotel_id=hotel_id,
        room_id=uuid4(),
        start_time=datetime.utcnow() + timedelta(days=1),
        end_time=datetime.utcnow() + timedelta(days=3),
        total_price=Decimal("300.00"),
        status=BookingStatus.CONFIRMED,
    )
    booking2 = Booking(
        id=uuid4(),
        user_id=uuid4(),
        hotel_id=hotel_id,
        room_id=uuid4(),
        start_time=datetime.utcnow() + timedelta(days=5),
        end_time=datetime.utcnow() + timedelta(days=7),
        total_price=Decimal("400.00"),
        status=BookingStatus.PENDING,
    )
    repo.bookings = [booking1, booking2]

    result = await use_case.execute(hotel_id)

    assert len(result) == 2
