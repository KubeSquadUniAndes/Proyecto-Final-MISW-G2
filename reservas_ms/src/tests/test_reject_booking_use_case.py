"""Unit tests for RejectBookingUseCase."""

from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from src.application.dtos.booking_dto import RejectBookingDTO
from src.application.use_cases.reject_booking import RejectBookingUseCase
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
async def test_reject_booking_success():
    """Test successful rejection of a pending booking."""
    # Arrange
    repo = MockBookingRepository()
    booking_id = uuid4()
    user_id = uuid4()
    admin_id = uuid4()
    hotel_id = uuid4()
    room_id = uuid4()

    booking = Booking(
        id=booking_id,
        user_id=user_id,
        hotel_id=hotel_id,
        room_id=room_id,
        start_time=datetime.utcnow() + timedelta(days=1),
        end_time=datetime.utcnow() + timedelta(days=3),
        status=BookingStatus.PENDING,
        price_per_night=Decimal("100.00"),
    )
    await repo.save(booking)

    use_case = RejectBookingUseCase(repo)
    dto = RejectBookingDTO(
        booking_id=booking_id,
        admin_user_id=admin_id,
        rejection_reason="Room not available due to maintenance",
    )

    # Act
    result = await use_case.execute(dto)

    # Assert
    assert result.id == booking_id
    assert result.status == BookingStatus.CANCELLED
    assert repo.bookings[booking_id].status == BookingStatus.CANCELLED
    assert "REJECTED by admin" in result.notes
    assert "maintenance" in result.notes


@pytest.mark.asyncio
async def test_reject_booking_not_found():
    """Test rejection fails when booking doesn't exist."""
    # Arrange
    repo = MockBookingRepository()
    use_case = RejectBookingUseCase(repo)
    dto = RejectBookingDTO(
        booking_id=uuid4(),
        admin_user_id=uuid4(),
        rejection_reason="Test reason",
    )

    # Act & Assert
    with pytest.raises(LookupError, match="not found"):
        await use_case.execute(dto)


@pytest.mark.asyncio
async def test_reject_booking_not_pending():
    """Test rejection fails when booking is not in pending status."""
    # Arrange
    repo = MockBookingRepository()
    booking_id = uuid4()
    user_id = uuid4()
    admin_id = uuid4()
    hotel_id = uuid4()
    room_id = uuid4()

    booking = Booking(
        id=booking_id,
        user_id=user_id,
        hotel_id=hotel_id,
        room_id=room_id,
        start_time=datetime.utcnow() + timedelta(days=1),
        end_time=datetime.utcnow() + timedelta(days=3),
        status=BookingStatus.CONFIRMED,  # Already confirmed
    )
    await repo.save(booking)

    use_case = RejectBookingUseCase(repo)
    dto = RejectBookingDTO(
        booking_id=booking_id,
        admin_user_id=admin_id,
        rejection_reason="Test reason",
    )

    # Act & Assert
    with pytest.raises(ValueError, match="Only pending bookings can be rejected"):
        await use_case.execute(dto)


@pytest.mark.asyncio
async def test_reject_booking_already_cancelled():
    """Test rejection fails when booking is already cancelled."""
    # Arrange
    repo = MockBookingRepository()
    booking_id = uuid4()
    user_id = uuid4()
    admin_id = uuid4()
    hotel_id = uuid4()
    room_id = uuid4()

    booking = Booking(
        id=booking_id,
        user_id=user_id,
        hotel_id=hotel_id,
        room_id=room_id,
        start_time=datetime.utcnow() + timedelta(days=1),
        end_time=datetime.utcnow() + timedelta(days=3),
        status=BookingStatus.CANCELLED,
    )
    await repo.save(booking)

    use_case = RejectBookingUseCase(repo)
    dto = RejectBookingDTO(
        booking_id=booking_id,
        admin_user_id=admin_id,
        rejection_reason="Test reason",
    )

    # Act & Assert
    with pytest.raises(ValueError, match="Only pending bookings can be rejected"):
        await use_case.execute(dto)


@pytest.mark.asyncio
async def test_reject_booking_appends_to_existing_notes():
    """Test that rejection reason is appended to existing notes."""
    # Arrange
    repo = MockBookingRepository()
    booking_id = uuid4()
    user_id = uuid4()
    admin_id = uuid4()
    hotel_id = uuid4()
    room_id = uuid4()

    booking = Booking(
        id=booking_id,
        user_id=user_id,
        hotel_id=hotel_id,
        room_id=room_id,
        start_time=datetime.utcnow() + timedelta(days=1),
        end_time=datetime.utcnow() + timedelta(days=3),
        status=BookingStatus.PENDING,
        notes="Original traveler notes",
    )
    await repo.save(booking)

    use_case = RejectBookingUseCase(repo)
    dto = RejectBookingDTO(
        booking_id=booking_id,
        admin_user_id=admin_id,
        rejection_reason="Overbooking issue",
    )

    # Act
    result = await use_case.execute(dto)

    # Assert
    assert "Original traveler notes" in result.notes
    assert "REJECTED by admin" in result.notes
    assert "Overbooking issue" in result.notes


@pytest.mark.asyncio
async def test_reject_booking_updates_timestamp():
    """Test that rejection updates the updated_at timestamp."""
    # Arrange
    repo = MockBookingRepository()
    booking_id = uuid4()
    user_id = uuid4()
    admin_id = uuid4()
    hotel_id = uuid4()
    room_id = uuid4()

    original_time = datetime.utcnow() - timedelta(hours=1)
    booking = Booking(
        id=booking_id,
        user_id=user_id,
        hotel_id=hotel_id,
        room_id=room_id,
        start_time=datetime.utcnow() + timedelta(days=1),
        end_time=datetime.utcnow() + timedelta(days=3),
        status=BookingStatus.PENDING,
        created_at=original_time,
        updated_at=original_time,
    )
    await repo.save(booking)

    use_case = RejectBookingUseCase(repo)
    dto = RejectBookingDTO(
        booking_id=booking_id,
        admin_user_id=admin_id,
        rejection_reason="Test reason",
    )

    # Act
    result = await use_case.execute(dto)

    # Assert
    assert result.updated_at > original_time
    assert repo.bookings[booking_id].updated_at > original_time


@pytest.mark.asyncio
async def test_reject_booking_with_empty_reason():
    """Test rejection with empty reason string."""
    # Arrange
    repo = MockBookingRepository()
    booking_id = uuid4()
    user_id = uuid4()
    admin_id = uuid4()
    hotel_id = uuid4()
    room_id = uuid4()

    booking = Booking(
        id=booking_id,
        user_id=user_id,
        hotel_id=hotel_id,
        room_id=room_id,
        start_time=datetime.utcnow() + timedelta(days=1),
        end_time=datetime.utcnow() + timedelta(days=3),
        status=BookingStatus.PENDING,
    )
    await repo.save(booking)

    use_case = RejectBookingUseCase(repo)
    dto = RejectBookingDTO(
        booking_id=booking_id,
        admin_user_id=admin_id,
        rejection_reason="",
    )

    # Act
    result = await use_case.execute(dto)

    # Assert
    assert result.status == BookingStatus.CANCELLED
    assert "REJECTED by admin" in result.notes
