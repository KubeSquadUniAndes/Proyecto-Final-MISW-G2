"""Unit tests for QR-related behaviour on the Booking domain entity."""

from datetime import datetime, timedelta
from uuid import uuid4

from src.domain.entities.booking import Booking, BookingStatus


def _make_booking(**overrides) -> Booking:
    defaults = dict(
        user_id=uuid4(),
        hotel_id=uuid4(),
        room_id=uuid4(),
        start_time=datetime.utcnow() + timedelta(days=1),
        end_time=datetime.utcnow() + timedelta(days=3),
        status=BookingStatus.CONFIRMED,
    )
    defaults.update(overrides)
    return Booking(**defaults)


# ── Default values ─────────────────────────────────────────────────────────────


def test_new_booking_has_no_qr_code():
    booking = _make_booking()
    assert booking.qr_code is None


def test_new_booking_has_no_qr_generated_at():
    booking = _make_booking()
    assert booking.qr_generated_at is None


def test_new_booking_qr_is_valid_by_default():
    """qr_is_valid defaults to True so the field is ready once QR is assigned."""
    booking = _make_booking()
    assert booking.qr_is_valid is True


# ── invalidate_qr ─────────────────────────────────────────────────────────────


def test_invalidate_qr_sets_flag_false():
    booking = _make_booking(qr_code="base64data==", qr_is_valid=True)
    booking.invalidate_qr()
    assert booking.qr_is_valid is False


def test_invalidate_qr_updates_timestamp():
    original_time = datetime.utcnow() - timedelta(seconds=5)
    booking = _make_booking(
        qr_code="base64data==",
        qr_is_valid=True,
        updated_at=original_time,
    )
    booking.invalidate_qr()
    assert booking.updated_at > original_time


def test_invalidate_qr_preserves_qr_code_content():
    """Invalidating the QR should not erase the code (hotel may log it)."""
    qr_content = "some_base64_content=="
    booking = _make_booking(qr_code=qr_content)
    booking.invalidate_qr()
    assert booking.qr_code == qr_content


def test_invalidate_qr_without_qr_code_does_not_raise():
    """Calling invalidate_qr on a booking with no QR must not raise."""
    booking = _make_booking(qr_code=None)
    booking.invalidate_qr()  # should not raise
    assert booking.qr_is_valid is False


def test_invalidate_qr_idempotent():
    """Calling invalidate_qr twice should remain valid=False without error."""
    booking = _make_booking(qr_code="base64data==")
    booking.invalidate_qr()
    booking.invalidate_qr()
    assert booking.qr_is_valid is False


# ── Integration with cancel / reject transitions ──────────────────────────────


def test_cancel_confirmed_booking_keeps_qr_code_accessible():
    """The entity cancel() itself does not touch QR — the use case does."""
    booking = _make_booking(
        status=BookingStatus.CONFIRMED,
        qr_code="base64data==",
        qr_is_valid=True,
    )
    booking.cancel()
    # Entity cancel() only changes status; QR invalidation is the use-case's job
    assert booking.status == BookingStatus.CANCELLED
    assert booking.qr_code == "base64data=="


def test_confirm_sets_status_not_qr():
    """Entity confirm() only changes status; QR generation is the use-case's job."""
    booking = _make_booking(status=BookingStatus.PENDING)
    booking.confirm()
    assert booking.status == BookingStatus.CONFIRMED
    assert booking.qr_code is None
    assert booking.qr_is_valid is True
