"""Unit tests for ApproveBookingUseCase."""

from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from src.application.dtos.booking_dto import ApproveBookingDTO
from src.application.use_cases.approve_booking import ApproveBookingUseCase
from src.domain.entities.booking import Booking, BookingStatus


class MockBookingRepository:
    """Mock repository for testing."""

    def __init__(self):
        self.bookings = {}

    async def get_by_id(self, booking_id):
        return self.bookings.get(booking_id)

    async def update(self, booking):
        self.bookings[booking.id] = booking
        return booking

    async def save(self, booking):
        self.bookings[booking.id] = booking
        return booking


@pytest.mark.asyncio
async def test_approve_booking_success():
    """Test successful approval of a pending booking."""
    # Arrange
    repo = MockBookingRepository()
    booking_id = uuid4()
    user_id = uuid4()
    admin_id = uuid4()
    resource_id = uuid4()

    booking = Booking(
        id=booking_id,
        user_id=user_id,
        resource_id=resource_id,
        start_time=datetime.utcnow() + timedelta(days=1),
        end_time=datetime.utcnow() + timedelta(days=3),
        status=BookingStatus.PENDING,
        price_per_night=Decimal("100.00"),
    )
    await repo.save(booking)

    use_case = ApproveBookingUseCase(repo)
    dto = ApproveBookingDTO(booking_id=booking_id, admin_user_id=admin_id)

    # Act
    result = await use_case.execute(dto)

    # Assert
    assert result.id == booking_id
    assert result.status == BookingStatus.CONFIRMED
    assert repo.bookings[booking_id].status == BookingStatus.CONFIRMED


@pytest.mark.asyncio
async def test_approve_booking_not_found():
    """Test approval fails when booking doesn't exist."""
    # Arrange
    repo = MockBookingRepository()
    use_case = ApproveBookingUseCase(repo)
    dto = ApproveBookingDTO(booking_id=uuid4(), admin_user_id=uuid4())

    # Act & Assert
    with pytest.raises(LookupError, match="not found"):
        await use_case.execute(dto)


@pytest.mark.asyncio
async def test_approve_booking_not_pending():
    """Test approval fails when booking is not in pending status."""
    # Arrange
    repo = MockBookingRepository()
    booking_id = uuid4()
    user_id = uuid4()
    admin_id = uuid4()
    resource_id = uuid4()

    booking = Booking(
        id=booking_id,
        user_id=user_id,
        resource_id=resource_id,
        start_time=datetime.utcnow() + timedelta(days=1),
        end_time=datetime.utcnow() + timedelta(days=3),
        status=BookingStatus.CONFIRMED,  # Already confirmed
    )
    await repo.save(booking)

    use_case = ApproveBookingUseCase(repo)
    dto = ApproveBookingDTO(booking_id=booking_id, admin_user_id=admin_id)

    # Act & Assert
    with pytest.raises(ValueError, match="Only pending bookings can be approved"):
        await use_case.execute(dto)


@pytest.mark.asyncio
async def test_approve_booking_cancelled():
    """Test approval fails when booking is cancelled."""
    # Arrange
    repo = MockBookingRepository()
    booking_id = uuid4()
    user_id = uuid4()
    admin_id = uuid4()
    resource_id = uuid4()

    booking = Booking(
        id=booking_id,
        user_id=user_id,
        resource_id=resource_id,
        start_time=datetime.utcnow() + timedelta(days=1),
        end_time=datetime.utcnow() + timedelta(days=3),
        status=BookingStatus.CANCELLED,
    )
    await repo.save(booking)

    use_case = ApproveBookingUseCase(repo)
    dto = ApproveBookingDTO(booking_id=booking_id, admin_user_id=admin_id)

    # Act & Assert
    with pytest.raises(ValueError, match="Only pending bookings can be approved"):
        await use_case.execute(dto)


@pytest.mark.asyncio
async def test_approve_booking_updates_timestamp():
    """Test that approval updates the updated_at timestamp."""
    # Arrange
    repo = MockBookingRepository()
    booking_id = uuid4()
    user_id = uuid4()
    admin_id = uuid4()
    resource_id = uuid4()

    original_time = datetime.utcnow() - timedelta(hours=1)
    booking = Booking(
        id=booking_id,
        user_id=user_id,
        resource_id=resource_id,
        start_time=datetime.utcnow() + timedelta(days=1),
        end_time=datetime.utcnow() + timedelta(days=3),
        status=BookingStatus.PENDING,
        created_at=original_time,
        updated_at=original_time,
    )
    await repo.save(booking)

    use_case = ApproveBookingUseCase(repo)
    dto = ApproveBookingDTO(booking_id=booking_id, admin_user_id=admin_id)

    # Act
    result = await use_case.execute(dto)

    # Assert
    assert result.updated_at > original_time
    assert repo.bookings[booking_id].updated_at > original_time
