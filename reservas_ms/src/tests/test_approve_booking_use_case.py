"""Unit tests for ApproveBookingUseCase."""

from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch
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

    use_case = ApproveBookingUseCase(repo)
    dto = ApproveBookingDTO(booking_id=booking_id, admin_user_id=admin_id)

    # Act
    result = await use_case.execute(dto)

    # Assert
    assert result.updated_at > original_time
    assert repo.bookings[booking_id].updated_at > original_time


# ── QR code generation (criteria 1, 3, 7) ────────────────────────────────────


def _make_pending_booking(**overrides) -> Booking:
    defaults = dict(
        id=uuid4(),
        user_id=uuid4(),
        hotel_id=uuid4(),
        room_id=uuid4(),
        start_time=datetime.utcnow() + timedelta(days=1),
        end_time=datetime.utcnow() + timedelta(days=3),
        status=BookingStatus.PENDING,
        booking_code="TH-2026-AB3XY",
        room_type="Doble estándar",
        traveler_name="Juan Pérez",
        traveler_email="juan@example.com",
    )
    defaults.update(overrides)
    return Booking(**defaults)


@pytest.mark.asyncio
async def test_approve_booking_generates_qr():
    """Approving a booking must result in qr_code being populated."""
    repo = MockBookingRepository()
    booking = _make_pending_booking()
    await repo.save(booking)

    with patch(
        "src.infrastructure.services.qr_generator.generate_booking_qr",
        return_value="FAKE_QR_BASE64==",
    ):
        use_case = ApproveBookingUseCase(repo)
        result = await use_case.execute(
            ApproveBookingDTO(booking_id=booking.id, admin_user_id=uuid4())
        )

    assert result.qr_code == "FAKE_QR_BASE64=="


@pytest.mark.asyncio
async def test_approve_booking_qr_is_valid():
    """QR must be marked valid right after generation."""
    repo = MockBookingRepository()
    booking = _make_pending_booking()
    await repo.save(booking)

    with patch(
        "src.infrastructure.services.qr_generator.generate_booking_qr",
        return_value="FAKE_QR_BASE64==",
    ):
        use_case = ApproveBookingUseCase(repo)
        result = await use_case.execute(
            ApproveBookingDTO(booking_id=booking.id, admin_user_id=uuid4())
        )

    assert result.qr_is_valid is True


@pytest.mark.asyncio
async def test_approve_booking_qr_generated_at_is_set():
    """qr_generated_at must be populated after approval."""
    repo = MockBookingRepository()
    booking = _make_pending_booking()
    await repo.save(booking)

    before = datetime.utcnow()
    with patch(
        "src.infrastructure.services.qr_generator.generate_booking_qr",
        return_value="FAKE_QR_BASE64==",
    ):
        use_case = ApproveBookingUseCase(repo)
        result = await use_case.execute(
            ApproveBookingDTO(booking_id=booking.id, admin_user_id=uuid4())
        )
    after = datetime.utcnow()

    assert result.qr_generated_at is not None
    assert before <= result.qr_generated_at <= after


@pytest.mark.asyncio
async def test_approve_booking_qr_generation_failure_does_not_fail_approval():
    """Criteria 7: if QR generation raises, the booking must still be confirmed."""
    repo = MockBookingRepository()
    booking = _make_pending_booking()
    await repo.save(booking)

    with patch(
        "src.infrastructure.services.qr_generator.generate_booking_qr",
        side_effect=RuntimeError("QR service unavailable"),
    ):
        use_case = ApproveBookingUseCase(repo)
        result = await use_case.execute(
            ApproveBookingDTO(booking_id=booking.id, admin_user_id=uuid4())
        )

    assert result.status == BookingStatus.CONFIRMED
    assert result.qr_code is None


@pytest.mark.asyncio
async def test_approve_booking_qr_uses_booking_code_as_identifier():
    """The QR generator must be called with the booking's own code."""
    repo = MockBookingRepository()
    booking = _make_pending_booking(booking_code="TH-2026-MYCODE")
    await repo.save(booking)

    with patch(
        "src.infrastructure.services.qr_generator.generate_booking_qr",
        return_value="FAKE==",
    ) as mock_gen:
        use_case = ApproveBookingUseCase(repo)
        await use_case.execute(
            ApproveBookingDTO(booking_id=booking.id, admin_user_id=uuid4())
        )

    mock_gen.assert_called_once()
    call_kwargs = mock_gen.call_args.kwargs
    assert call_kwargs["booking_code"] == "TH-2026-MYCODE"


@pytest.mark.asyncio
async def test_approve_booking_qr_saved_to_repository():
    """The generated QR must be persisted in the repository."""
    repo = MockBookingRepository()
    booking = _make_pending_booking()
    await repo.save(booking)

    with patch(
        "src.infrastructure.services.qr_generator.generate_booking_qr",
        return_value="SAVED_QR==",
    ):
        use_case = ApproveBookingUseCase(repo)
        await use_case.execute(
            ApproveBookingDTO(booking_id=booking.id, admin_user_id=uuid4())
        )

    saved = repo.bookings[booking.id]
    assert saved.qr_code == "SAVED_QR=="
