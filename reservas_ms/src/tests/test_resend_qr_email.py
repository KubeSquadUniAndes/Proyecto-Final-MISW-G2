"""Unit tests for ResendQrEmailUseCase."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.application.use_cases.resend_qr_email import ResendQrEmailUseCase
from src.domain.entities.booking import Booking, BookingStatus


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_booking(**overrides) -> Booking:
    from datetime import datetime, timedelta

    base = dict(
        user_id=uuid4(),
        hotel_id=uuid4(),
        room_id=uuid4(),
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow() + timedelta(days=3),
        status=BookingStatus.CONFIRMED,
        booking_code="TH-2026-QR01",
        qr_code="FAKE_QR_BASE64==",
        qr_is_valid=True,
        traveler_name="Ana Torres",
        traveler_email="ana@example.com",
        room_type="Doble estándar",
        num_guests=2,
    )
    base.update(overrides)
    return Booking(**base)


def _make_use_case(booking: Booking | None, email_sent: bool = True):
    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = booking
    mock_notif = AsyncMock()
    mock_notif.send_qr_checkin_email.return_value = email_sent
    return ResendQrEmailUseCase(mock_repo, mock_notif), mock_repo, mock_notif


# ── Not found ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_raises_lookup_error_when_booking_not_found():
    use_case, _, _ = _make_use_case(None)
    with pytest.raises(LookupError):
        await use_case.execute(uuid4(), uuid4())


# ── Ownership ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_raises_permission_error_wrong_user():
    booking = _make_booking()
    use_case, _, _ = _make_use_case(booking)
    with pytest.raises(PermissionError):
        await use_case.execute(booking.id, uuid4())  # different user


# ── QR missing ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_raises_value_error_when_no_qr_code():
    booking = _make_booking(qr_code=None)
    use_case, _, _ = _make_use_case(booking)
    with pytest.raises(ValueError, match="no tiene un código QR"):
        await use_case.execute(booking.id, booking.user_id)


# ── QR invalid ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_raises_value_error_when_qr_not_valid():
    booking = _make_booking(qr_is_valid=False)
    use_case, _, _ = _make_use_case(booking)
    with pytest.raises(ValueError, match="invalidado"):
        await use_case.execute(booking.id, booking.user_id)


# ── Bad status ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_raises_value_error_when_status_is_pending():
    booking = _make_booking(status=BookingStatus.PENDING)
    use_case, _, _ = _make_use_case(booking)
    with pytest.raises(ValueError, match="estado"):
        await use_case.execute(booking.id, booking.user_id)


@pytest.mark.asyncio
async def test_raises_value_error_when_status_is_cancelled():
    booking = _make_booking(status=BookingStatus.CANCELLED, qr_is_valid=False)
    use_case, _, _ = _make_use_case(booking)
    # qr_is_valid=False will be caught first
    with pytest.raises(ValueError):
        await use_case.execute(booking.id, booking.user_id)


# ── No email ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_raises_value_error_when_no_traveler_email():
    booking = _make_booking(traveler_email=None)
    use_case, _, _ = _make_use_case(booking)
    with pytest.raises(ValueError, match="correo"):
        await use_case.execute(booking.id, booking.user_id)


# ── Happy path ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_returns_true_when_email_sent():
    booking = _make_booking()
    use_case, _, mock_notif = _make_use_case(booking, email_sent=True)
    result = await use_case.execute(booking.id, booking.user_id)
    assert result is True
    mock_notif.send_qr_checkin_email.assert_awaited_once()


@pytest.mark.asyncio
async def test_returns_false_when_email_service_fails():
    booking = _make_booking()
    use_case, _, _ = _make_use_case(booking, email_sent=False)
    result = await use_case.execute(booking.id, booking.user_id)
    assert result is False


@pytest.mark.asyncio
async def test_check_in_status_also_allowed():
    booking = _make_booking(status=BookingStatus.CHECK_IN)
    use_case, _, mock_notif = _make_use_case(booking, email_sent=True)
    result = await use_case.execute(booking.id, booking.user_id)
    assert result is True
    mock_notif.send_qr_checkin_email.assert_awaited_once()


@pytest.mark.asyncio
async def test_correct_payload_sent_to_notif_client():
    booking = _make_booking()
    use_case, _, mock_notif = _make_use_case(booking, email_sent=True)
    await use_case.execute(booking.id, booking.user_id)

    call_kwargs = mock_notif.send_qr_checkin_email.call_args.kwargs
    assert call_kwargs["reservation_code"] == str(booking.booking_code or booking.id)
    assert call_kwargs["guest_email"] == booking.traveler_email
    assert call_kwargs["qr_code"] == booking.qr_code
