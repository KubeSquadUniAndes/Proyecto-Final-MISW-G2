"""Tests for UpdateBooking use case and Booking entity methods."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.application.dtos.booking_dto import UpdateBookingDTO
from src.application.use_cases.update_booking import UpdateBookingUseCase
from src.domain.entities.booking import Booking, BookingStatus
from src.domain.services.booking_domain_service import BookingDomainService


@pytest.fixture
def user_id():
    return uuid4()


@pytest.fixture
def resource_id():
    return uuid4()


@pytest.fixture
def now():
    return datetime.utcnow()


@pytest.fixture
def existing_booking(user_id, resource_id, now):
    return Booking(
        user_id=user_id,
        resource_id=resource_id,
        start_time=now + timedelta(hours=1),
        end_time=now + timedelta(hours=3),
    )


@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.fixture
def use_case(mock_repo):
    domain_service = BookingDomainService(mock_repo)
    return UpdateBookingUseCase(mock_repo, domain_service)


# ── UpdateBookingUseCase ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_booking_success(
    use_case, mock_repo, existing_booking, user_id, now
):
    new_end = now + timedelta(hours=4)
    mock_repo.get_by_id.return_value = existing_booking
    mock_repo.list_by_user.return_value = []
    mock_repo.update.return_value = existing_booking

    dto = UpdateBookingDTO(
        booking_id=existing_booking.id,
        user_id=user_id,
        end_time=new_end,
        notes="updated notes",
    )
    result = await use_case.execute(dto)

    assert result.user_id == user_id
    mock_repo.update.assert_called_once()


@pytest.mark.asyncio
async def test_update_booking_not_found(use_case, mock_repo, user_id):
    mock_repo.get_by_id.return_value = None

    with pytest.raises(ValueError, match="not found"):
        await use_case.execute(UpdateBookingDTO(booking_id=uuid4(), user_id=user_id))


@pytest.mark.asyncio
async def test_update_booking_wrong_owner(use_case, mock_repo, existing_booking):
    mock_repo.get_by_id.return_value = existing_booking

    with pytest.raises(PermissionError, match="permission"):
        await use_case.execute(
            UpdateBookingDTO(booking_id=existing_booking.id, user_id=uuid4())
        )


@pytest.mark.asyncio
async def test_update_booking_invalid_dates(
    use_case, mock_repo, existing_booking, user_id
):
    # Force invalid dates directly on the entity so domain validation triggers
    existing_booking.start_time, existing_booking.end_time = (
        existing_booking.end_time,
        existing_booking.start_time,
    )
    mock_repo.get_by_id.return_value = existing_booking
    mock_repo.list_by_user.return_value = []

    dto = UpdateBookingDTO(booking_id=existing_booking.id, user_id=user_id)
    with pytest.raises(ValueError, match="not valid"):
        await use_case.execute(dto)


@pytest.mark.asyncio
async def test_update_booking_schedule_conflict(
    use_case, mock_repo, existing_booking, user_id, resource_id, now
):
    conflicting = Booking(
        user_id=user_id,
        resource_id=resource_id,
        start_time=now + timedelta(hours=2),
        end_time=now + timedelta(hours=5),
    )
    mock_repo.get_by_id.return_value = existing_booking
    mock_repo.list_by_user.return_value = [conflicting]

    dto = UpdateBookingDTO(
        booking_id=existing_booking.id,
        user_id=user_id,
        start_time=now + timedelta(hours=2),
        end_time=now + timedelta(hours=4),
    )
    with pytest.raises(ValueError, match="conflict"):
        await use_case.execute(dto)


@pytest.mark.asyncio
async def test_update_booking_with_anomaly_client(
    mock_repo, existing_booking, user_id, now
):
    mock_repo.get_by_id.return_value = existing_booking
    mock_repo.list_by_user.return_value = []
    mock_repo.update.return_value = existing_booking

    anomaly_client = AsyncMock()
    anomaly_client.analyze.return_value = {"is_anomalous": False}

    domain_service = BookingDomainService(mock_repo)
    use_case = UpdateBookingUseCase(
        mock_repo, domain_service, anomaly_client=anomaly_client
    )

    dto = UpdateBookingDTO(
        booking_id=existing_booking.id,
        user_id=user_id,
        notes="with anomaly check",
    )
    result = await use_case.execute(dto)
    assert result is not None
    anomaly_client.analyze.assert_called_once()


@pytest.mark.asyncio
async def test_update_booking_anomaly_client_raises(
    mock_repo, existing_booking, user_id
):
    mock_repo.get_by_id.return_value = existing_booking
    mock_repo.list_by_user.return_value = []

    anomaly_client = AsyncMock()
    anomaly_client.analyze.side_effect = Exception("connection error")

    domain_service = BookingDomainService(mock_repo)
    use_case = UpdateBookingUseCase(
        mock_repo, domain_service, anomaly_client=anomaly_client
    )

    with pytest.raises(ValueError, match="anomaly_check_failed"):
        await use_case.execute(
            UpdateBookingDTO(booking_id=existing_booking.id, user_id=user_id)
        )


# ── Booking entity methods ────────────────────────────────────────────────────


def test_booking_confirm(existing_booking):
    existing_booking.confirm()
    assert existing_booking.status == BookingStatus.CONFIRMED


def test_booking_confirm_invalid_status(existing_booking):
    existing_booking.status = BookingStatus.CANCELLED
    with pytest.raises(ValueError, match="Cannot confirm"):
        existing_booking.confirm()


def test_booking_cancel(existing_booking):
    existing_booking.cancel()
    assert existing_booking.status == BookingStatus.CANCELLED


def test_booking_cancel_already_cancelled(existing_booking):
    existing_booking.status = BookingStatus.CANCELLED
    with pytest.raises(ValueError, match="Cannot cancel"):
        existing_booking.cancel()


def test_booking_complete(existing_booking):
    existing_booking.status = BookingStatus.CONFIRMED
    existing_booking.complete()
    assert existing_booking.status == BookingStatus.COMPLETED


def test_booking_complete_invalid_status(existing_booking):
    with pytest.raises(ValueError, match="Cannot complete"):
        existing_booking.complete()


def test_booking_is_valid_false(existing_booking):
    existing_booking.start_time, existing_booking.end_time = (
        existing_booking.end_time,
        existing_booking.start_time,
    )
    assert existing_booking.is_valid() is False
