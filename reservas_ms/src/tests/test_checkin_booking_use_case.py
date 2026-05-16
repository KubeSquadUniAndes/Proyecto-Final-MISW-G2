"""Unit tests for CheckInBookingUseCase — covers all 8 acceptance criteria."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from src.application.dtos.booking_dto import CheckInBookingDTO
from src.application.use_cases.checkin_booking import CheckInBookingUseCase
from src.domain.entities.booking import Booking, BookingStatus


# ── Helpers ───────────────────────────────────────────────────────────────────

TODAY_STR = datetime.utcnow().strftime("%Y-%m-%d")
TODAY_DATE = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
PAST_DATE = TODAY_DATE - timedelta(days=1)
FUTURE_DATE = TODAY_DATE + timedelta(days=1)


def _confirmed_booking(**overrides) -> Booking:
    defaults = dict(
        user_id=uuid4(),
        hotel_id=uuid4(),
        room_id=uuid4(),
        start_time=TODAY_DATE,
        end_time=TODAY_DATE + timedelta(days=3),
        status=BookingStatus.CONFIRMED,
        booking_code="TH-2026-TEST1",
        qr_code="FAKE_QR_BASE64==",
        qr_is_valid=True,
        traveler_name="Ana Torres",
        room_type="Doble estándar",
        num_guests=2,
    )
    defaults.update(overrides)
    return Booking(**defaults)


def _make_dto(**overrides) -> CheckInBookingDTO:
    defaults = dict(
        booking_code="TH-2026-TEST1",
        booking_id=uuid4(),
        staff_id="staff-001",
        device="iPad Recepción",
        ip="192.168.1.10",
    )
    defaults.update(overrides)
    return CheckInBookingDTO(**defaults)


def _make_use_case(booking: Booking | None, update_return: Booking | None = None):
    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = booking
    mock_repo.update.return_value = update_return or booking
    return CheckInBookingUseCase(mock_repo), mock_repo


# ── C1: Escaneo exitoso y actualización de estado ─────────────────────────────


@pytest.mark.asyncio
async def test_checkin_transitions_to_checked_in():
    booking = _confirmed_booking()
    use_case, mock_repo = _make_use_case(booking)
    dto = _make_dto(booking_id=booking.id, booking_code=booking.booking_code)

    with patch("src.application.use_cases.checkin_booking.date") as mock_date:
        mock_date.today.return_value = TODAY_DATE.date()
        result = await use_case.execute(dto)

    assert result.status == BookingStatus.CHECK_IN


@pytest.mark.asyncio
async def test_checkin_returns_full_booking_details():
    booking = _confirmed_booking()
    use_case, _ = _make_use_case(booking)
    dto = _make_dto(booking_id=booking.id, booking_code=booking.booking_code)

    with patch("src.application.use_cases.checkin_booking.date") as mock_date:
        mock_date.today.return_value = TODAY_DATE.date()
        result = await use_case.execute(dto)

    assert result.booking_code == booking.booking_code
    assert result.traveler_name == booking.traveler_name
    assert result.room_type == booking.room_type
    assert result.num_guests == booking.num_guests


@pytest.mark.asyncio
async def test_checkin_saves_to_repository():
    booking = _confirmed_booking()
    use_case, mock_repo = _make_use_case(booking)
    dto = _make_dto(booking_id=booking.id, booking_code=booking.booking_code)

    with patch("src.application.use_cases.checkin_booking.date") as mock_date:
        mock_date.today.return_value = TODAY_DATE.date()
        await use_case.execute(dto)

    mock_repo.update.assert_called_once()


# ── C2 / C3: Validación de fecha ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_checkin_allowed_on_checkin_date():
    booking = _confirmed_booking(start_time=TODAY_DATE)
    use_case, _ = _make_use_case(booking)
    dto = _make_dto(booking_id=booking.id, booking_code=booking.booking_code)

    with patch("src.application.use_cases.checkin_booking.date") as mock_date:
        mock_date.today.return_value = TODAY_DATE.date()
        result = await use_case.execute(dto)

    assert result.status == BookingStatus.CHECK_IN


@pytest.mark.asyncio
async def test_checkin_rejected_when_date_is_future():
    booking = _confirmed_booking(start_time=FUTURE_DATE)
    use_case, mock_repo = _make_use_case(booking)
    dto = _make_dto(booking_id=booking.id, booking_code=booking.booking_code)

    with patch("src.application.use_cases.checkin_booking.date") as mock_date:
        mock_date.today.return_value = TODAY_DATE.date()
        with pytest.raises(ValueError, match="aún no está disponible"):
            await use_case.execute(dto)

    mock_repo.update.assert_not_called()


@pytest.mark.asyncio
async def test_checkin_allowed_when_start_is_past_but_still_within_stay():
    """Guest arrives a day late — check-in allowed as long as today <= checkout."""
    booking = _confirmed_booking(
        start_time=PAST_DATE,
        end_time=TODAY_DATE + timedelta(days=2),
    )
    use_case, mock_repo = _make_use_case(booking)
    dto = _make_dto(booking_id=booking.id, booking_code=booking.booking_code)

    with patch("src.application.use_cases.checkin_booking.date") as mock_date:
        mock_date.today.return_value = TODAY_DATE.date()
        result = await use_case.execute(dto)

    assert result.status == BookingStatus.CHECK_IN
    mock_repo.update.assert_called_once()


@pytest.mark.asyncio
async def test_checkin_rejected_when_past_checkout_date():
    """QR expired: today is after the checkout date."""
    booking = _confirmed_booking(
        start_time=PAST_DATE - timedelta(days=3),
        end_time=PAST_DATE,
    )
    use_case, mock_repo = _make_use_case(booking)
    dto = _make_dto(booking_id=booking.id, booking_code=booking.booking_code)

    with patch("src.application.use_cases.checkin_booking.date") as mock_date:
        mock_date.today.return_value = TODAY_DATE.date()
        with pytest.raises(ValueError, match="expirado"):
            await use_case.execute(dto)

    mock_repo.update.assert_not_called()


@pytest.mark.asyncio
async def test_checkin_date_error_does_not_modify_status():
    booking = _confirmed_booking(start_time=FUTURE_DATE)
    original_status = booking.status
    use_case, _ = _make_use_case(booking)
    dto = _make_dto(booking_id=booking.id, booking_code=booking.booking_code)

    with patch("src.application.use_cases.checkin_booking.date") as mock_date:
        mock_date.today.return_value = TODAY_DATE.date()
        with pytest.raises(ValueError):
            await use_case.execute(dto)

    assert booking.status == original_status


# ── C4: QR inválido o expirado ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_checkin_rejected_when_qr_is_invalid():
    booking = _confirmed_booking(qr_is_valid=False)
    use_case, mock_repo = _make_use_case(booking)
    dto = _make_dto(booking_id=booking.id, booking_code=booking.booking_code)

    with patch("src.application.use_cases.checkin_booking.date") as mock_date:
        mock_date.today.return_value = TODAY_DATE.date()
        with pytest.raises(ValueError, match="invalidado"):
            await use_case.execute(dto)

    mock_repo.update.assert_not_called()


@pytest.mark.asyncio
async def test_checkin_rejected_when_booking_is_cancelled():
    booking = _confirmed_booking(status=BookingStatus.CANCELLED)
    use_case, mock_repo = _make_use_case(booking)
    dto = _make_dto(booking_id=booking.id, booking_code=booking.booking_code)

    with pytest.raises(ValueError, match="cancelada"):
        await use_case.execute(dto)

    mock_repo.update.assert_not_called()


@pytest.mark.asyncio
async def test_checkin_rejected_when_no_qr_code():
    booking = _confirmed_booking(qr_code=None)
    use_case, mock_repo = _make_use_case(booking)
    dto = _make_dto(booking_id=booking.id, booking_code=booking.booking_code)

    with patch("src.application.use_cases.checkin_booking.date") as mock_date:
        mock_date.today.return_value = TODAY_DATE.date()
        with pytest.raises(ValueError, match="no tiene un código QR"):
            await use_case.execute(dto)

    mock_repo.update.assert_not_called()


@pytest.mark.asyncio
async def test_checkin_rejected_when_booking_code_mismatch():
    booking = _confirmed_booking(booking_code="TH-2026-REAL1")
    use_case, mock_repo = _make_use_case(booking)
    dto = _make_dto(booking_id=booking.id, booking_code="TH-2026-FAKE9")

    with pytest.raises(ValueError, match="no corresponde"):
        await use_case.execute(dto)

    mock_repo.update.assert_not_called()


# ── C5: Check-in ya realizado ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_checkin_rejected_when_already_checked_in():
    booking = _confirmed_booking(
        status=BookingStatus.CHECK_IN,
        checked_in_at=datetime.utcnow() - timedelta(hours=1),
    )
    use_case, mock_repo = _make_use_case(booking)
    dto = _make_dto(booking_id=booking.id, booking_code=booking.booking_code)

    with pytest.raises(ValueError, match="ya fue registrado"):
        await use_case.execute(dto)

    mock_repo.update.assert_not_called()


@pytest.mark.asyncio
async def test_checkin_already_done_message_includes_timestamp():
    ts = datetime(2026, 6, 10, 14, 32, 0)
    booking = _confirmed_booking(status=BookingStatus.CHECK_IN, checked_in_at=ts)
    use_case, _ = _make_use_case(booking)
    dto = _make_dto(booking_id=booking.id, booking_code=booking.booking_code)

    with pytest.raises(ValueError) as exc_info:
        await use_case.execute(dto)

    assert "2026-06-10" in str(exc_info.value)


# ── C6: Notificación al viajero ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_checkin_sends_push_notification():
    booking = _confirmed_booking()
    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = booking
    mock_repo.update.return_value = booking

    mock_notif = AsyncMock()
    mock_notif.send_booking_notification.return_value = True
    mock_users = AsyncMock()
    mock_users.get_fcm_token.return_value = "fcm-token-abc"

    use_case = CheckInBookingUseCase(mock_repo, mock_notif, mock_users)
    dto = _make_dto(booking_id=booking.id, booking_code=booking.booking_code)

    with patch("src.application.use_cases.checkin_booking.date") as mock_date:
        mock_date.today.return_value = TODAY_DATE.date()
        await use_case.execute(dto)

    mock_notif.send_booking_notification.assert_called_once()
    call_kwargs = mock_notif.send_booking_notification.call_args.kwargs
    assert call_kwargs["event_type"] == "checkin"


@pytest.mark.asyncio
async def test_checkin_notification_failure_does_not_raise():
    booking = _confirmed_booking()
    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = booking
    mock_repo.update.return_value = booking

    mock_notif = AsyncMock()
    mock_notif.send_booking_notification.side_effect = RuntimeError("FCM down")
    mock_users = AsyncMock()
    mock_users.get_fcm_token.return_value = "fcm-token-abc"

    use_case = CheckInBookingUseCase(mock_repo, mock_notif, mock_users)
    dto = _make_dto(booking_id=booking.id, booking_code=booking.booking_code)

    with patch("src.application.use_cases.checkin_booking.date") as mock_date:
        mock_date.today.return_value = TODAY_DATE.date()
        result = await use_case.execute(dto)  # must not raise

    assert result.status == BookingStatus.CHECK_IN


@pytest.mark.asyncio
async def test_checkin_skips_notification_when_no_fcm_token():
    booking = _confirmed_booking()
    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = booking
    mock_repo.update.return_value = booking

    mock_notif = AsyncMock()
    mock_users = AsyncMock()
    mock_users.get_fcm_token.return_value = None  # no token

    use_case = CheckInBookingUseCase(mock_repo, mock_notif, mock_users)
    dto = _make_dto(booking_id=booking.id, booking_code=booking.booking_code)

    with patch("src.application.use_cases.checkin_booking.date") as mock_date:
        mock_date.today.return_value = TODAY_DATE.date()
        await use_case.execute(dto)

    mock_notif.send_booking_notification.assert_not_called()


# ── C7: Auditoría ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_checkin_records_checked_in_at():
    booking = _confirmed_booking()
    use_case, mock_repo = _make_use_case(booking)
    dto = _make_dto(booking_id=booking.id, booking_code=booking.booking_code)

    with patch("src.application.use_cases.checkin_booking.date") as mock_date:
        mock_date.today.return_value = TODAY_DATE.date()
        await use_case.execute(dto)

    saved: Booking = mock_repo.update.call_args[0][0]
    assert saved.checked_in_at is not None


@pytest.mark.asyncio
async def test_checkin_records_staff_id():
    booking = _confirmed_booking()
    use_case, mock_repo = _make_use_case(booking)
    dto = _make_dto(
        booking_id=booking.id, booking_code=booking.booking_code, staff_id="staff-999"
    )

    with patch("src.application.use_cases.checkin_booking.date") as mock_date:
        mock_date.today.return_value = TODAY_DATE.date()
        await use_case.execute(dto)

    saved: Booking = mock_repo.update.call_args[0][0]
    assert saved.checkin_staff_id == "staff-999"


@pytest.mark.asyncio
async def test_checkin_records_device():
    booking = _confirmed_booking()
    use_case, mock_repo = _make_use_case(booking)
    dto = _make_dto(
        booking_id=booking.id,
        booking_code=booking.booking_code,
        device="iPad Pro Recepción",
    )

    with patch("src.application.use_cases.checkin_booking.date") as mock_date:
        mock_date.today.return_value = TODAY_DATE.date()
        await use_case.execute(dto)

    saved: Booking = mock_repo.update.call_args[0][0]
    assert saved.checkin_device == "iPad Pro Recepción"


@pytest.mark.asyncio
async def test_checkin_records_ip():
    booking = _confirmed_booking()
    use_case, mock_repo = _make_use_case(booking)
    dto = _make_dto(
        booking_id=booking.id, booking_code=booking.booking_code, ip="10.0.0.42"
    )

    with patch("src.application.use_cases.checkin_booking.date") as mock_date:
        mock_date.today.return_value = TODAY_DATE.date()
        await use_case.execute(dto)

    saved: Booking = mock_repo.update.call_args[0][0]
    assert saved.checkin_ip == "10.0.0.42"


# ── C8: Booking no encontrado ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_checkin_raises_lookup_error_when_not_found():
    use_case, _ = _make_use_case(booking=None)
    dto = _make_dto()

    with pytest.raises(LookupError, match="not found"):
        await use_case.execute(dto)


# ── Entidad: método check_in ──────────────────────────────────────────────────


def test_entity_checkin_transitions_status():
    booking = _confirmed_booking()
    booking.check_in()
    assert booking.status == BookingStatus.CHECK_IN


def test_entity_checkin_sets_checked_in_at():
    booking = _confirmed_booking()
    before = datetime.utcnow()
    booking.check_in()
    assert booking.checked_in_at is not None
    assert booking.checked_in_at >= before


def test_entity_checkin_stores_audit_fields():
    booking = _confirmed_booking()
    booking.check_in(staff_id="s1", device="tablet", ip="1.2.3.4")
    assert booking.checkin_staff_id == "s1"
    assert booking.checkin_device == "tablet"
    assert booking.checkin_ip == "1.2.3.4"


def test_entity_checkin_from_non_confirmed_raises():
    booking = _confirmed_booking(status=BookingStatus.PENDING)
    with pytest.raises(ValueError, match="Cannot check-in"):
        booking.check_in()


def test_entity_cancel_checked_in_booking_raises():
    booking = _confirmed_booking(status=BookingStatus.CHECK_IN)
    with pytest.raises(ValueError):
        booking.cancel()


def test_entity_checkin_not_cancellable():
    booking = _confirmed_booking(status=BookingStatus.CHECK_IN)
    assert booking.cancellable is False


def test_entity_checkin_status_display():
    booking = _confirmed_booking(status=BookingStatus.CHECK_IN)
    assert booking.status_display == "Check-In realizado"
