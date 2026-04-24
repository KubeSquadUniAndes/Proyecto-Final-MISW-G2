"""Unit tests for Booking entity reject method."""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from src.domain.entities.booking import Booking, BookingStatus


def test_reject_pending_booking():
    """Test rejecting a pending booking changes status to cancelled."""
    booking = Booking(
        user_id=uuid4(),
        hotel_id=uuid4(),
        room_id=uuid4(),
        start_time=datetime.utcnow() + timedelta(days=1),
        end_time=datetime.utcnow() + timedelta(days=3),
        status=BookingStatus.PENDING,
    )

    original_updated_at = booking.updated_at
    booking.reject()

    assert booking.status == BookingStatus.CANCELLED
    assert booking.updated_at > original_updated_at


def test_reject_confirmed_booking_fails():
    """Test rejecting a confirmed booking raises ValueError."""
    booking = Booking(
        user_id=uuid4(),
        hotel_id=uuid4(),
        room_id=uuid4(),
        start_time=datetime.utcnow() + timedelta(days=1),
        end_time=datetime.utcnow() + timedelta(days=3),
        status=BookingStatus.CONFIRMED,
    )

    with pytest.raises(ValueError, match="Cannot reject a booking with status"):
        booking.reject()


def test_reject_cancelled_booking_fails():
    """Test rejecting an already cancelled booking raises ValueError."""
    booking = Booking(
        user_id=uuid4(),
        hotel_id=uuid4(),
        room_id=uuid4(),
        start_time=datetime.utcnow() + timedelta(days=1),
        end_time=datetime.utcnow() + timedelta(days=3),
        status=BookingStatus.CANCELLED,
    )

    with pytest.raises(ValueError, match="Cannot reject a booking with status"):
        booking.reject()


def test_reject_completed_booking_fails():
    """Test rejecting a completed booking raises ValueError."""
    booking = Booking(
        user_id=uuid4(),
        hotel_id=uuid4(),
        room_id=uuid4(),
        start_time=datetime.utcnow() - timedelta(days=3),
        end_time=datetime.utcnow() - timedelta(days=1),
        status=BookingStatus.COMPLETED,
    )

    with pytest.raises(ValueError, match="Cannot reject a booking with status"):
        booking.reject()


def test_confirm_and_reject_flow():
    """Test that a booking can be confirmed but not rejected after confirmation."""
    booking = Booking(
        user_id=uuid4(),
        hotel_id=uuid4(),
        room_id=uuid4(),
        start_time=datetime.utcnow() + timedelta(days=1),
        end_time=datetime.utcnow() + timedelta(days=3),
        status=BookingStatus.PENDING,
    )

    # Confirm should work
    booking.confirm()
    assert booking.status == BookingStatus.CONFIRMED

    # Reject should fail
    with pytest.raises(ValueError, match="Cannot reject a booking with status"):
        booking.reject()
