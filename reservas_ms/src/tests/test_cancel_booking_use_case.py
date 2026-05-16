"""Unit tests for CancelBookingUseCase."""

from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from src.application.dtos.booking_dto import CancelBookingDTO
from src.application.use_cases.cancel_booking import CancelBookingUseCase
from src.domain.entities.booking import Booking, BookingStatus


class MockBookingRepository:
    def __init__(self):
        self.bookings = {}

    async def get_by_id(self, booking_id):
        return self.bookings.get(booking_id)

    async def update(self, booking):
        self.bookings[booking.id] = booking
        return booking


@pytest.mark.asyncio
async def test_cancel_booking_success():
    """Test successful booking cancellation."""
    repo = MockBookingRepository()
    use_case = CancelBookingUseCase(repo)

    booking_id = uuid4()
    user_id = uuid4()
    booking = Booking(
        id=booking_id,
        user_id=user_id,
        hotel_id=uuid4(),
        room_id=uuid4(),
        start_time=datetime.utcnow() + timedelta(days=1),
        end_time=datetime.utcnow() + timedelta(days=3),
        total_price=Decimal("300.00"),
        status=BookingStatus.PENDING,
    )
    repo.bookings[booking_id] = booking

    dto = CancelBookingDTO(booking_id=booking_id, user_id=user_id)
    result = await use_case.execute(dto)

    assert result.status == "cancelled"
    assert repo.bookings[booking_id].status == BookingStatus.CANCELLED


@pytest.mark.asyncio
async def test_cancel_booking_not_found():
    """Test cancellation fails when booking doesn't exist."""
    repo = MockBookingRepository()
    use_case = CancelBookingUseCase(repo)

    dto = CancelBookingDTO(booking_id=uuid4(), user_id=uuid4())

    with pytest.raises(LookupError, match="not found"):
        await use_case.execute(dto)


@pytest.mark.asyncio
async def test_cancel_booking_wrong_user():
    """Test cancellation fails when user doesn't own booking."""
    repo = MockBookingRepository()
    use_case = CancelBookingUseCase(repo)

    booking_id = uuid4()
    owner_id = uuid4()
    other_user_id = uuid4()

    booking = Booking(
        id=booking_id,
        user_id=owner_id,
        hotel_id=uuid4(),
        room_id=uuid4(),
        start_time=datetime.utcnow() + timedelta(days=1),
        end_time=datetime.utcnow() + timedelta(days=3),
        total_price=Decimal("300.00"),
        status=BookingStatus.PENDING,
    )
    repo.bookings[booking_id] = booking

    dto = CancelBookingDTO(booking_id=booking_id, user_id=other_user_id)

    with pytest.raises(PermissionError, match="do not have permission"):
        await use_case.execute(dto)


@pytest.mark.asyncio
async def test_cancel_booking_not_cancellable():
    """Test cancellation fails when booking is already cancelled."""
    repo = MockBookingRepository()
    use_case = CancelBookingUseCase(repo)

    booking_id = uuid4()
    user_id = uuid4()

    booking = Booking(
        id=booking_id,
        user_id=user_id,
        hotel_id=uuid4(),
        room_id=uuid4(),
        start_time=datetime.utcnow() + timedelta(days=1),
        end_time=datetime.utcnow() + timedelta(days=3),
        total_price=Decimal("300.00"),
        status=BookingStatus.CANCELLED,
    )
    repo.bookings[booking_id] = booking

    dto = CancelBookingDTO(booking_id=booking_id, user_id=user_id)

    with pytest.raises(ValueError, match="Cannot cancel"):
        await use_case.execute(dto)


# ── QR invalidation on cancel (criteria 5) ────────────────────────────────────


@pytest.mark.asyncio
async def test_cancel_confirmed_booking_invalidates_qr():
    """Cancelling a confirmed booking with a QR must set qr_is_valid=False."""
    repo = MockBookingRepository()
    use_case = CancelBookingUseCase(repo)

    booking_id = uuid4()
    user_id = uuid4()

    booking = Booking(
        id=booking_id,
        user_id=user_id,
        hotel_id=uuid4(),
        room_id=uuid4(),
        start_time=datetime.utcnow() + timedelta(days=1),
        end_time=datetime.utcnow() + timedelta(days=3),
        status=BookingStatus.CONFIRMED,
        qr_code="SOME_BASE64_QR==",
        qr_is_valid=True,
    )
    repo.bookings[booking_id] = booking

    dto = CancelBookingDTO(booking_id=booking_id, user_id=user_id)
    result = await use_case.execute(dto)

    assert result.status == "cancelled"
    assert result.qr_is_valid is False
    assert repo.bookings[booking_id].qr_is_valid is False


@pytest.mark.asyncio
async def test_cancel_confirmed_booking_preserves_qr_code_value():
    """After invalidation the qr_code bytes must still be present (for audit)."""
    repo = MockBookingRepository()
    use_case = CancelBookingUseCase(repo)

    booking_id = uuid4()
    user_id = uuid4()
    qr_content = "SOME_BASE64_QR=="

    booking = Booking(
        id=booking_id,
        user_id=user_id,
        hotel_id=uuid4(),
        room_id=uuid4(),
        start_time=datetime.utcnow() + timedelta(days=1),
        end_time=datetime.utcnow() + timedelta(days=3),
        status=BookingStatus.CONFIRMED,
        qr_code=qr_content,
        qr_is_valid=True,
    )
    repo.bookings[booking_id] = booking

    dto = CancelBookingDTO(booking_id=booking_id, user_id=user_id)
    result = await use_case.execute(dto)

    assert result.qr_code == qr_content


@pytest.mark.asyncio
async def test_cancel_pending_booking_without_qr_succeeds():
    """Cancelling a pending booking that never had a QR must not raise."""
    repo = MockBookingRepository()
    use_case = CancelBookingUseCase(repo)

    booking_id = uuid4()
    user_id = uuid4()

    booking = Booking(
        id=booking_id,
        user_id=user_id,
        hotel_id=uuid4(),
        room_id=uuid4(),
        start_time=datetime.utcnow() + timedelta(days=1),
        end_time=datetime.utcnow() + timedelta(days=3),
        status=BookingStatus.PENDING,
        qr_code=None,
    )
    repo.bookings[booking_id] = booking

    dto = CancelBookingDTO(booking_id=booking_id, user_id=user_id)
    result = await use_case.execute(dto)

    assert result.status == "cancelled"
    assert result.qr_code is None
