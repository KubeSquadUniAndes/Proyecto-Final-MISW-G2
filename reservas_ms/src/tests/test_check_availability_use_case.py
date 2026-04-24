"""Unit tests for CheckAvailabilityUseCase."""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from src.application.dtos.availability_dto import AvailabilityQueryDTO
from src.application.use_cases.check_availability import CheckAvailabilityUseCase
from src.domain.entities.booking import Booking, BookingStatus


class MockBookingRepository:
    """Mock repository for testing."""

    def __init__(self):
        self.bookings = []

    async def get_by_resource_and_date_range(self, resource_id, start_time, end_time):
        """Return bookings that overlap with the date range."""
        return [
            b
            for b in self.bookings
            if b.resource_id == resource_id
            and b.start_time < end_time
            and b.end_time > start_time
        ]

    def add_booking(self, booking):
        self.bookings.append(booking)


@pytest.mark.asyncio
async def test_check_availability_no_bookings():
    """Test availability check when no bookings exist."""
    # Arrange
    repo = MockBookingRepository()
    resource_id = uuid4()
    start_time = datetime.utcnow() + timedelta(days=1)
    end_time = datetime.utcnow() + timedelta(days=5)

    use_case = CheckAvailabilityUseCase(repo)
    dto = AvailabilityQueryDTO(
        resource_id=resource_id,
        start_time=start_time,
        end_time=end_time,
    )

    # Act
    result = await use_case.execute(dto)

    # Assert
    assert result.resource_id == resource_id
    assert result.total_bookings == 0
    assert len(result.bookings) == 0
    assert result.summary["confirmed"] == 0
    assert result.summary["pending"] == 0


@pytest.mark.asyncio
async def test_check_availability_with_bookings():
    """Test availability check with existing bookings."""
    # Arrange
    repo = MockBookingRepository()
    resource_id = uuid4()
    user_id = uuid4()

    start_time = datetime.utcnow() + timedelta(days=1)
    end_time = datetime.utcnow() + timedelta(days=10)

    # Add confirmed booking
    booking1 = Booking(
        id=uuid4(),
        user_id=user_id,
        resource_id=resource_id,
        start_time=datetime.utcnow() + timedelta(days=2),
        end_time=datetime.utcnow() + timedelta(days=4),
        status=BookingStatus.CONFIRMED,
        room_type="Deluxe",
        num_guests=2,
        booking_code="BK001",
        traveler_name="John Doe",
    )
    repo.add_booking(booking1)

    # Add pending booking
    booking2 = Booking(
        id=uuid4(),
        user_id=user_id,
        resource_id=resource_id,
        start_time=datetime.utcnow() + timedelta(days=6),
        end_time=datetime.utcnow() + timedelta(days=8),
        status=BookingStatus.PENDING,
        room_type="Suite",
        num_guests=4,
        booking_code="BK002",
        traveler_name="Jane Smith",
    )
    repo.add_booking(booking2)

    use_case = CheckAvailabilityUseCase(repo)
    dto = AvailabilityQueryDTO(
        resource_id=resource_id,
        start_time=start_time,
        end_time=end_time,
    )

    # Act
    result = await use_case.execute(dto)

    # Assert
    assert result.resource_id == resource_id
    assert result.total_bookings == 2
    assert len(result.bookings) == 2
    assert result.summary["confirmed"] == 1
    assert result.summary["pending"] == 1
    assert result.summary["cancelled"] == 0


@pytest.mark.asyncio
async def test_check_availability_filter_by_room_type():
    """Test availability check filtered by room type."""
    # Arrange
    repo = MockBookingRepository()
    resource_id = uuid4()
    user_id = uuid4()

    start_time = datetime.utcnow() + timedelta(days=1)
    end_time = datetime.utcnow() + timedelta(days=10)

    # Add Deluxe booking
    booking1 = Booking(
        id=uuid4(),
        user_id=user_id,
        resource_id=resource_id,
        start_time=datetime.utcnow() + timedelta(days=2),
        end_time=datetime.utcnow() + timedelta(days=4),
        status=BookingStatus.CONFIRMED,
        room_type="Deluxe",
        num_guests=2,
    )
    repo.add_booking(booking1)

    # Add Suite booking
    booking2 = Booking(
        id=uuid4(),
        user_id=user_id,
        resource_id=resource_id,
        start_time=datetime.utcnow() + timedelta(days=6),
        end_time=datetime.utcnow() + timedelta(days=8),
        status=BookingStatus.CONFIRMED,
        room_type="Suite",
        num_guests=4,
    )
    repo.add_booking(booking2)

    use_case = CheckAvailabilityUseCase(repo)
    dto = AvailabilityQueryDTO(
        resource_id=resource_id,
        start_time=start_time,
        end_time=end_time,
        room_type="Deluxe",
    )

    # Act
    result = await use_case.execute(dto)

    # Assert
    assert result.total_bookings == 1
    assert result.bookings[0].room_type == "Deluxe"
    assert result.filters["room_type"] == "Deluxe"


@pytest.mark.asyncio
async def test_check_availability_filter_by_status():
    """Test availability check filtered by status."""
    # Arrange
    repo = MockBookingRepository()
    resource_id = uuid4()
    user_id = uuid4()

    start_time = datetime.utcnow() + timedelta(days=1)
    end_time = datetime.utcnow() + timedelta(days=10)

    # Add confirmed booking
    booking1 = Booking(
        id=uuid4(),
        user_id=user_id,
        resource_id=resource_id,
        start_time=datetime.utcnow() + timedelta(days=2),
        end_time=datetime.utcnow() + timedelta(days=4),
        status=BookingStatus.CONFIRMED,
        room_type="Deluxe",
        num_guests=2,
    )
    repo.add_booking(booking1)

    # Add pending booking
    booking2 = Booking(
        id=uuid4(),
        user_id=user_id,
        resource_id=resource_id,
        start_time=datetime.utcnow() + timedelta(days=6),
        end_time=datetime.utcnow() + timedelta(days=8),
        status=BookingStatus.PENDING,
        room_type="Suite",
        num_guests=4,
    )
    repo.add_booking(booking2)

    use_case = CheckAvailabilityUseCase(repo)
    dto = AvailabilityQueryDTO(
        resource_id=resource_id,
        start_time=start_time,
        end_time=end_time,
        status=BookingStatus.CONFIRMED,
    )

    # Act
    result = await use_case.execute(dto)

    # Assert
    assert result.total_bookings == 1
    assert result.bookings[0].status == BookingStatus.CONFIRMED
    assert result.summary["confirmed"] == 1
    assert result.summary["pending"] == 0


@pytest.mark.asyncio
async def test_check_availability_different_resource():
    """Test that bookings from different resources are not returned."""
    # Arrange
    repo = MockBookingRepository()
    resource_id_1 = uuid4()
    resource_id_2 = uuid4()
    user_id = uuid4()

    start_time = datetime.utcnow() + timedelta(days=1)
    end_time = datetime.utcnow() + timedelta(days=10)

    # Add booking for resource 1
    booking1 = Booking(
        id=uuid4(),
        user_id=user_id,
        resource_id=resource_id_1,
        start_time=datetime.utcnow() + timedelta(days=2),
        end_time=datetime.utcnow() + timedelta(days=4),
        status=BookingStatus.CONFIRMED,
        room_type="Deluxe",
        num_guests=2,
    )
    repo.add_booking(booking1)

    # Add booking for resource 2
    booking2 = Booking(
        id=uuid4(),
        user_id=user_id,
        resource_id=resource_id_2,
        start_time=datetime.utcnow() + timedelta(days=6),
        end_time=datetime.utcnow() + timedelta(days=8),
        status=BookingStatus.CONFIRMED,
        room_type="Suite",
        num_guests=4,
    )
    repo.add_booking(booking2)

    use_case = CheckAvailabilityUseCase(repo)
    dto = AvailabilityQueryDTO(
        resource_id=resource_id_1,
        start_time=start_time,
        end_time=end_time,
    )

    # Act
    result = await use_case.execute(dto)

    # Assert
    assert result.total_bookings == 1
    assert result.bookings[0].id == booking1.id


@pytest.mark.asyncio
async def test_check_availability_no_overlap():
    """Test that bookings outside the date range are not returned."""
    # Arrange
    repo = MockBookingRepository()
    resource_id = uuid4()
    user_id = uuid4()

    # Query range: days 10-15
    start_time = datetime.utcnow() + timedelta(days=10)
    end_time = datetime.utcnow() + timedelta(days=15)

    # Add booking before query range (days 2-4)
    booking1 = Booking(
        id=uuid4(),
        user_id=user_id,
        resource_id=resource_id,
        start_time=datetime.utcnow() + timedelta(days=2),
        end_time=datetime.utcnow() + timedelta(days=4),
        status=BookingStatus.CONFIRMED,
        room_type="Deluxe",
        num_guests=2,
    )
    repo.add_booking(booking1)

    # Add booking after query range (days 20-25)
    booking2 = Booking(
        id=uuid4(),
        user_id=user_id,
        resource_id=resource_id,
        start_time=datetime.utcnow() + timedelta(days=20),
        end_time=datetime.utcnow() + timedelta(days=25),
        status=BookingStatus.CONFIRMED,
        room_type="Suite",
        num_guests=4,
    )
    repo.add_booking(booking2)

    use_case = CheckAvailabilityUseCase(repo)
    dto = AvailabilityQueryDTO(
        resource_id=resource_id,
        start_time=start_time,
        end_time=end_time,
    )

    # Act
    result = await use_case.execute(dto)

    # Assert
    assert result.total_bookings == 0
    assert len(result.bookings) == 0


@pytest.mark.asyncio
async def test_check_availability_invalid_date_range():
    """Test that end_time before start_time raises error."""
    # Arrange
    resource_id = uuid4()

    start_time = datetime.utcnow() + timedelta(days=10)
    end_time = datetime.utcnow() + timedelta(days=5)  # Before start_time

    # Act & Assert
    with pytest.raises(ValueError, match="end_time must be after start_time"):
        AvailabilityQueryDTO(
            resource_id=resource_id,
            start_time=start_time,
            end_time=end_time,
        )
