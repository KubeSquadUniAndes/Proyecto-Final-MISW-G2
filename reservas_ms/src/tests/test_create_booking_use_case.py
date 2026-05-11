"""Tests for the CreateBooking use case using mocks."""

from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.application.dtos.booking_dto import CreateBookingDTO
from src.application.use_cases.create_booking import (
    CreateBookingUseCase,
    _payment_status_display,
)
from src.domain.entities.booking import Booking, BookingStatus
from src.domain.services.booking_domain_service import BookingDomainService


@pytest.fixture
def user_id():
    return uuid4()


@pytest.fixture
def hotel_id():
    return uuid4()


@pytest.fixture
def room_id():
    return uuid4()


@pytest.fixture
def valid_times():
    now = datetime.utcnow()
    return now, now + timedelta(days=3)


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    repo.list_by_user.return_value = []
    return repo


@pytest.fixture
def use_case(mock_repo):
    domain_service = BookingDomainService(mock_repo)
    return CreateBookingUseCase(mock_repo, domain_service)


@pytest.mark.asyncio
async def test_create_booking_success(
    use_case, mock_repo, user_id, hotel_id, room_id, valid_times
):
    start_time, end_time = valid_times

    # Arrange
    expected_booking = Booking(
        user_id=user_id,
        hotel_id=hotel_id,
        room_id=room_id,
        start_time=start_time,
        end_time=end_time,
        booking_code="TH-2026-TEST1",
    )
    mock_repo.save.return_value = expected_booking

    dto = CreateBookingDTO(
        user_id=user_id,
        hotel_id=hotel_id,
        room_id=room_id,
        start_time=start_time,
        end_time=end_time,
    )

    # Act
    result = await use_case.execute(dto)

    # Assert
    assert result.user_id == user_id
    assert result.hotel_id == hotel_id
    assert result.room_id == room_id
    assert result.status == BookingStatus.PENDING
    mock_repo.save.assert_called_once()


@pytest.mark.asyncio
async def test_create_booking_with_schedule_conflict(
    use_case, mock_repo, user_id, hotel_id, room_id, valid_times
):
    start_time, end_time = valid_times

    # Arrange: an existing booking occupies the same slot
    existing_booking = Booking(
        user_id=user_id,
        hotel_id=hotel_id,
        room_id=room_id,
        start_time=start_time,
        end_time=end_time,
    )
    mock_repo.list_by_user.return_value = [existing_booking]

    dto = CreateBookingDTO(
        user_id=user_id,
        hotel_id=hotel_id,
        room_id=room_id,
        start_time=start_time,
        end_time=end_time,
    )

    # Act & Assert
    with pytest.raises(ValueError, match="schedule conflict"):
        await use_case.execute(dto)

    mock_repo.save.assert_not_called()


def test_payment_status_display_none():
    assert _payment_status_display(None) is None


def test_payment_status_display_known():
    assert _payment_status_display("pending") == "Pendiente de pago"
    assert _payment_status_display("confirmed") == "Pago confirmado"


def test_payment_status_display_unknown():
    assert _payment_status_display("unknown_status") == "unknown_status"


@pytest.mark.asyncio
async def test_create_booking_same_day_raises(mock_repo, user_id, hotel_id, room_id):
    now = datetime.utcnow()
    start = now.replace(hour=10, minute=0, second=0, microsecond=0)
    end = now.replace(hour=22, minute=0, second=0, microsecond=0)
    domain_service = BookingDomainService(mock_repo)
    uc = CreateBookingUseCase(mock_repo, domain_service)
    dto = CreateBookingDTO(
        user_id=user_id,
        hotel_id=hotel_id,
        room_id=room_id,
        start_time=start,
        end_time=end,
    )
    with pytest.raises(ValueError, match="at least 1 night"):
        await uc.execute(dto)


@pytest.mark.asyncio
async def test_create_booking_anomaly_client_anomalous(
    mock_repo, user_id, hotel_id, room_id, valid_times
):
    start_time, end_time = valid_times
    booking = Booking(
        user_id=user_id, hotel_id=hotel_id, room_id=room_id,
        start_time=start_time, end_time=end_time, booking_code="TH-2026-ANOM1",
    )
    mock_repo.save.return_value = booking
    anomaly_client = AsyncMock()
    anomaly_client.analyze.return_value = {"is_anomalous": True, "action_taken": "flagged"}
    domain_service = BookingDomainService(mock_repo)
    uc = CreateBookingUseCase(mock_repo, domain_service, anomaly_client=anomaly_client)
    dto = CreateBookingDTO(
        user_id=user_id, hotel_id=hotel_id, room_id=room_id,
        start_time=start_time, end_time=end_time,
    )
    result = await uc.execute(dto)
    assert result.user_id == user_id
    anomaly_client.analyze.assert_called_once()


@pytest.mark.asyncio
async def test_create_booking_anomaly_client_exception(
    mock_repo, user_id, hotel_id, room_id, valid_times
):
    start_time, end_time = valid_times
    anomaly_client = AsyncMock()
    anomaly_client.analyze.side_effect = RuntimeError("service unavailable")
    domain_service = BookingDomainService(mock_repo)
    uc = CreateBookingUseCase(mock_repo, domain_service, anomaly_client=anomaly_client)
    dto = CreateBookingDTO(
        user_id=user_id, hotel_id=hotel_id, room_id=room_id,
        start_time=start_time, end_time=end_time,
    )
    with pytest.raises(ValueError, match="anomaly_check_failed"):
        await uc.execute(dto)


@pytest.mark.asyncio
async def test_create_booking_with_availability_publisher(
    mock_repo, user_id, hotel_id, room_id, valid_times
):
    start_time, end_time = valid_times
    booking = Booking(
        user_id=user_id, hotel_id=hotel_id, room_id=room_id,
        start_time=start_time, end_time=end_time, booking_code="TH-2026-PUB01",
    )
    mock_repo.save.return_value = booking
    publisher = AsyncMock()
    domain_service = BookingDomainService(mock_repo)
    uc = CreateBookingUseCase(mock_repo, domain_service, availability_publisher=publisher)
    dto = CreateBookingDTO(
        user_id=user_id, hotel_id=hotel_id, room_id=room_id,
        start_time=start_time, end_time=end_time,
    )
    result = await uc.execute(dto)
    assert result.user_id == user_id
    publisher.publish.assert_called_once()


@pytest.mark.asyncio
async def test_create_booking_publisher_exception_is_swallowed(
    mock_repo, user_id, hotel_id, room_id, valid_times
):
    start_time, end_time = valid_times
    booking = Booking(
        user_id=user_id, hotel_id=hotel_id, room_id=room_id,
        start_time=start_time, end_time=end_time, booking_code="TH-2026-PUB02",
    )
    mock_repo.save.return_value = booking
    publisher = AsyncMock()
    publisher.publish.side_effect = RuntimeError("sns down")
    domain_service = BookingDomainService(mock_repo)
    uc = CreateBookingUseCase(mock_repo, domain_service, availability_publisher=publisher)
    dto = CreateBookingDTO(
        user_id=user_id, hotel_id=hotel_id, room_id=room_id,
        start_time=start_time, end_time=end_time,
    )
    result = await uc.execute(dto)
    assert result.user_id == user_id

