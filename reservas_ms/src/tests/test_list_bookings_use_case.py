"""Unit tests for ListBookingsUseCase."""

from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from src.application.use_cases.list_bookings import ListBookingsUseCase
from src.domain.entities.booking import Booking, BookingStatus


class MockBookingRepository:
    def __init__(self):
        self.bookings = []

    async def get_active_by_user(self, user_id):
        return [b for b in self.bookings if b.user_id == user_id]


@pytest.mark.asyncio
async def test_list_bookings_success():
    """Test listing bookings for a user."""
    repo = MockBookingRepository()
    use_case = ListBookingsUseCase(repo)

    user_id = uuid4()
    booking1_id = uuid4()
    booking2_id = uuid4()
    booking1 = Booking(
        id=booking1_id,
        user_id=user_id,
        hotel_id=uuid4(),
        room_id=uuid4(),
        start_time=datetime.utcnow() + timedelta(days=1),
        end_time=datetime.utcnow() + timedelta(days=3),
        total_price=Decimal("300.00"),
        status=BookingStatus.CONFIRMED,
    )
    booking2 = Booking(
        id=booking2_id,
        user_id=user_id,
        hotel_id=uuid4(),
        room_id=uuid4(),
        start_time=datetime.utcnow() + timedelta(days=5),
        end_time=datetime.utcnow() + timedelta(days=7),
        total_price=Decimal("400.00"),
        status=BookingStatus.PENDING,
    )
    repo.bookings = [booking1, booking2]

    result = await use_case.execute(user_id)

    assert len(result) == 2
    assert result[0].id == booking1_id
    assert result[1].id == booking2_id


@pytest.mark.asyncio
async def test_list_bookings_empty():
    """Test listing bookings returns empty list when user has no bookings."""
    repo = MockBookingRepository()
    use_case = ListBookingsUseCase(repo)

    user_id = uuid4()
    result = await use_case.execute(user_id)

    assert len(result) == 0


@pytest.mark.asyncio
async def test_list_bookings_filters_by_user():
    """Test listing bookings only returns bookings for the specified user."""
    repo = MockBookingRepository()
    use_case = ListBookingsUseCase(repo)

    user1_id = uuid4()
    user2_id = uuid4()
    booking1_id = uuid4()

    booking1 = Booking(
        id=booking1_id,
        user_id=user1_id,
        hotel_id=uuid4(),
        room_id=uuid4(),
        start_time=datetime.utcnow() + timedelta(days=1),
        end_time=datetime.utcnow() + timedelta(days=3),
        total_price=Decimal("300.00"),
        status=BookingStatus.CONFIRMED,
    )
    booking2 = Booking(
        id=uuid4(),
        user_id=user2_id,
        hotel_id=uuid4(),
        room_id=uuid4(),
        start_time=datetime.utcnow() + timedelta(days=5),
        end_time=datetime.utcnow() + timedelta(days=7),
        total_price=Decimal("400.00"),
        status=BookingStatus.PENDING,
    )
    repo.bookings = [booking1, booking2]

    result = await use_case.execute(user1_id)

    assert len(result) == 1
    assert result[0].id == booking1_id
