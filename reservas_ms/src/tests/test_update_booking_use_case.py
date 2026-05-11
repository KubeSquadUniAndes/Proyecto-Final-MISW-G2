"""Tests for the UpdateBooking use case."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.application.dtos.booking_dto import UpdateBookingDTO
from src.application.use_cases.update_booking import UpdateBookingUseCase
from src.domain.entities.booking import Booking
from src.domain.services.booking_domain_service import BookingDomainService


def _make_booking(user_id=None, **kwargs):
    now = datetime.utcnow()
    defaults = dict(
        user_id=user_id or uuid4(),
        hotel_id=uuid4(),
        room_id=uuid4(),
        start_time=now + timedelta(days=1),
        end_time=now + timedelta(days=4),
        booking_code="TH-2026-ABCD1",
    )
    defaults.update(kwargs)
    return Booking(**defaults)


def _make_use_case(booking=None, conflict=False, anomaly_client=None, publisher=None):
    repo = AsyncMock()
    repo.get_by_id.return_value = booking
    repo.list_by_user.return_value = [booking] if conflict and booking else []
    repo.update.return_value = booking
    domain_service = BookingDomainService(repo)
    return UpdateBookingUseCase(repo, domain_service, anomaly_client, publisher), repo


@pytest.mark.asyncio
async def test_update_booking_not_found():
    uc, _ = _make_use_case(booking=None)
    dto = UpdateBookingDTO(booking_id=uuid4(), user_id=uuid4(), notes="hi")
    with pytest.raises(ValueError, match="not found"):
        await uc.execute(dto)


@pytest.mark.asyncio
async def test_update_booking_permission_error():
    booking = _make_booking()
    uc, _ = _make_use_case(booking=booking)
    dto = UpdateBookingDTO(booking_id=booking.id, user_id=uuid4(), notes="hi")
    with pytest.raises(PermissionError, match="permission"):
        await uc.execute(dto)


@pytest.mark.asyncio
async def test_update_booking_invalid_dates():
    now = datetime.utcnow()
    user_id = uuid4()
    booking = _make_booking(
        user_id=user_id,
        start_time=now + timedelta(days=2),
        end_time=now + timedelta(days=5),
    )
    uc, _ = _make_use_case(booking=booking)
    # Set end_time before start_time directly via UpdateBookingDTO fields
    # (bypassing DTO validator by setting independently)
    dto = UpdateBookingDTO(booking_id=booking.id, user_id=user_id)
    # Force invalid state on the booking after retrieval
    booking.start_time = now + timedelta(days=5)
    booking.end_time = now + timedelta(days=2)
    with pytest.raises(ValueError, match="not valid"):
        await uc.execute(dto)


@pytest.mark.asyncio
async def test_update_booking_conflict():
    now = datetime.utcnow()
    user_id = uuid4()
    room_id = uuid4()
    booking = _make_booking(
        user_id=user_id,
        room_id=room_id,
        start_time=now + timedelta(days=1),
        end_time=now + timedelta(days=4),
    )
    conflicting = _make_booking(
        user_id=user_id,
        room_id=room_id,
        start_time=now + timedelta(days=2),
        end_time=now + timedelta(days=5),
    )
    repo = AsyncMock()
    repo.get_by_id.return_value = booking
    repo.list_by_user.return_value = [conflicting]
    repo.update.return_value = booking
    domain_service = BookingDomainService(repo)
    uc = UpdateBookingUseCase(repo, domain_service)
    dto = UpdateBookingDTO(booking_id=booking.id, user_id=user_id)
    with pytest.raises(ValueError, match="conflict"):
        await uc.execute(dto)


@pytest.mark.asyncio
async def test_update_booking_success_updates_fields():
    now = datetime.utcnow()
    user_id = uuid4()
    booking = _make_booking(
        user_id=user_id,
        start_time=now + timedelta(days=1),
        end_time=now + timedelta(days=4),
    )
    uc, repo = _make_use_case(booking=booking)
    new_start = now + timedelta(days=2)
    new_end = now + timedelta(days=6)
    dto = UpdateBookingDTO(
        booking_id=booking.id,
        user_id=user_id,
        notes="Updated note",
        start_time=new_start,
        end_time=new_end,
    )
    result = await uc.execute(dto)
    assert result.user_id == user_id
    repo.update.assert_called_once()


@pytest.mark.asyncio
async def test_update_booking_with_anomaly_client_anomalous():
    now = datetime.utcnow()
    user_id = uuid4()
    booking = _make_booking(
        user_id=user_id,
        start_time=now + timedelta(days=1),
        end_time=now + timedelta(days=4),
    )
    anomaly_client = AsyncMock()
    anomaly_client.analyze.return_value = {
        "is_anomalous": True,
        "action_taken": "blocked",
    }
    uc, _ = _make_use_case(booking=booking, anomaly_client=anomaly_client)
    dto = UpdateBookingDTO(booking_id=booking.id, user_id=user_id)
    result = await uc.execute(dto)
    assert result.user_id == user_id
    anomaly_client.analyze.assert_called_once()


@pytest.mark.asyncio
async def test_update_booking_with_anomaly_client_exception():
    now = datetime.utcnow()
    user_id = uuid4()
    booking = _make_booking(
        user_id=user_id,
        start_time=now + timedelta(days=1),
        end_time=now + timedelta(days=4),
    )
    anomaly_client = AsyncMock()
    anomaly_client.analyze.side_effect = RuntimeError("service down")
    uc, _ = _make_use_case(booking=booking, anomaly_client=anomaly_client)
    dto = UpdateBookingDTO(booking_id=booking.id, user_id=user_id)
    with pytest.raises(ValueError, match="anomaly_check_failed"):
        await uc.execute(dto)


@pytest.mark.asyncio
async def test_update_booking_with_availability_publisher():
    now = datetime.utcnow()
    user_id = uuid4()
    booking = _make_booking(
        user_id=user_id,
        start_time=now + timedelta(days=1),
        end_time=now + timedelta(days=4),
    )
    publisher = AsyncMock()
    uc, _ = _make_use_case(booking=booking, publisher=publisher)
    dto = UpdateBookingDTO(booking_id=booking.id, user_id=user_id)
    result = await uc.execute(dto)
    assert result.user_id == user_id
    publisher.publish.assert_called_once()


@pytest.mark.asyncio
async def test_update_booking_publisher_exception_is_swallowed():
    now = datetime.utcnow()
    user_id = uuid4()
    booking = _make_booking(
        user_id=user_id,
        start_time=now + timedelta(days=1),
        end_time=now + timedelta(days=4),
    )
    publisher = AsyncMock()
    publisher.publish.side_effect = RuntimeError("sns down")
    uc, _ = _make_use_case(booking=booking, publisher=publisher)
    dto = UpdateBookingDTO(booking_id=booking.id, user_id=user_id)
    # Publisher errors must NOT propagate
    result = await uc.execute(dto)
    assert result.user_id == user_id
