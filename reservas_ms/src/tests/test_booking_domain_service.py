"""Unit tests for BookingDomainService."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from src.domain.entities.booking import Booking, BookingStatus
from src.domain.services.booking_domain_service import BookingDomainService


class MockBookingRepository:
    def __init__(self):
        self.bookings = []

    async def list_by_user(self, user_id):
        return [b for b in self.bookings if b.user_id == user_id]


@pytest.mark.asyncio
async def test_has_schedule_conflict_no_conflict():
    """Test no conflict when bookings don't overlap."""
    repo = MockBookingRepository()
    service = BookingDomainService(repo)

    user_id = uuid4()
    hotel_id = uuid4()
    room_id = uuid4()

    existing_booking = Booking(
        id=uuid4(),
        user_id=user_id,
        hotel_id=hotel_id,
        room_id=room_id,
        start_time=datetime.utcnow() + timedelta(days=1),
        end_time=datetime.utcnow() + timedelta(days=3),
        total_price=Decimal("300.00"),
        status=BookingStatus.CONFIRMED,
    )
    repo.bookings = [existing_booking]

    # New booking after existing one
    has_conflict = await service.has_schedule_conflict(
        user_id=user_id,
        room_id=room_id,
        start_time=datetime.utcnow() + timedelta(days=5),
        end_time=datetime.utcnow() + timedelta(days=7),
    )

    assert has_conflict is False


@pytest.mark.asyncio
async def test_has_schedule_conflict_with_overlap():
    """Test conflict detected when bookings overlap."""
    repo = MockBookingRepository()
    service = BookingDomainService(repo)

    user_id = uuid4()
    hotel_id = uuid4()
    room_id = uuid4()

    existing_booking = Booking(
        id=uuid4(),
        user_id=user_id,
        hotel_id=hotel_id,
        room_id=room_id,
        start_time=datetime.utcnow() + timedelta(days=1),
        end_time=datetime.utcnow() + timedelta(days=5),
        total_price=Decimal("300.00"),
        status=BookingStatus.CONFIRMED,
    )
    repo.bookings = [existing_booking]

    # New booking overlaps with existing one
    has_conflict = await service.has_schedule_conflict(
        user_id=user_id,
        room_id=room_id,
        start_time=datetime.utcnow() + timedelta(days=3),
        end_time=datetime.utcnow() + timedelta(days=7),
    )

    assert has_conflict is True


@pytest.mark.asyncio
async def test_has_schedule_conflict_different_resource():
    """Test no conflict when bookings are for different resources."""
    repo = MockBookingRepository()
    service = BookingDomainService(repo)

    user_id = uuid4()
    hotel_id = uuid4()
    room1_id = uuid4()
    room2_id = uuid4()

    existing_booking = Booking(
        id=uuid4(),
        user_id=user_id,
        hotel_id=hotel_id,
        room_id=room1_id,
        start_time=datetime.utcnow() + timedelta(days=1),
        end_time=datetime.utcnow() + timedelta(days=5),
        total_price=Decimal("300.00"),
        status=BookingStatus.CONFIRMED,
    )
    repo.bookings = [existing_booking]

    # New booking for different resource
    has_conflict = await service.has_schedule_conflict(
        user_id=user_id,
        room_id=room2_id,
        start_time=datetime.utcnow() + timedelta(days=2),
        end_time=datetime.utcnow() + timedelta(days=4),
    )

    assert has_conflict is False


@pytest.mark.asyncio
async def test_has_schedule_conflict_cancelled_booking_ignored():
    """Test cancelled bookings don't cause conflicts."""
    repo = MockBookingRepository()
    service = BookingDomainService(repo)

    user_id = uuid4()
    hotel_id = uuid4()
    room_id = uuid4()

    cancelled_booking = Booking(
        id=uuid4(),
        user_id=user_id,
        hotel_id=hotel_id,
        room_id=room_id,
        start_time=datetime.utcnow() + timedelta(days=1),
        end_time=datetime.utcnow() + timedelta(days=5),
        total_price=Decimal("300.00"),
        status=BookingStatus.CANCELLED,
    )
    repo.bookings = [cancelled_booking]

    # New booking overlaps with cancelled one
    has_conflict = await service.has_schedule_conflict(
        user_id=user_id,
        room_id=room_id,
        start_time=datetime.utcnow() + timedelta(days=2),
        end_time=datetime.utcnow() + timedelta(days=4),
    )

    assert has_conflict is False


@pytest.mark.asyncio
async def test_has_schedule_conflict_exclude_booking():
    """Test excluding a booking from conflict check."""
    repo = MockBookingRepository()
    service = BookingDomainService(repo)

    user_id = uuid4()
    hotel_id = uuid4()
    room_id = uuid4()
    booking_id = uuid4()

    existing_booking = Booking(
        id=booking_id,
        user_id=user_id,
        hotel_id=hotel_id,
        room_id=room_id,
        start_time=datetime.utcnow() + timedelta(days=1),
        end_time=datetime.utcnow() + timedelta(days=5),
        total_price=Decimal("300.00"),
        status=BookingStatus.CONFIRMED,
    )
    repo.bookings = [existing_booking]

    # Check same time range but exclude the existing booking
    has_conflict = await service.has_schedule_conflict(
        user_id=user_id,
        room_id=room_id,
        start_time=datetime.utcnow() + timedelta(days=2),
        end_time=datetime.utcnow() + timedelta(days=4),
        exclude_booking_id=booking_id,
    )

    assert has_conflict is False


@pytest.mark.asyncio
async def test_has_schedule_conflict_timezone_aware():
    """Test conflict detection with timezone-aware datetimes."""
    repo = MockBookingRepository()
    service = BookingDomainService(repo)

    user_id = uuid4()
    hotel_id = uuid4()
    room_id = uuid4()

    # Create booking with timezone-aware datetime
    existing_booking = Booking(
        id=uuid4(),
        user_id=user_id,
        hotel_id=hotel_id,
        room_id=room_id,
        start_time=datetime.now(timezone.utc) + timedelta(days=1),
        end_time=datetime.now(timezone.utc) + timedelta(days=5),
        total_price=Decimal("300.00"),
        status=BookingStatus.CONFIRMED,
    )
    repo.bookings = [existing_booking]

    # Check with timezone-aware datetimes
    has_conflict = await service.has_schedule_conflict(
        user_id=user_id,
        room_id=room_id,
        start_time=datetime.now(timezone.utc) + timedelta(days=3),
        end_time=datetime.now(timezone.utc) + timedelta(days=7),
    )

    assert has_conflict is True
