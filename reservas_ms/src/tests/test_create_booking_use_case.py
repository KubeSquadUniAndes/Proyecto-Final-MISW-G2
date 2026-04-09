"""Tests for the CreateBooking use case using mocks."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.application.dtos.booking_dto import CreateBookingDTO
from src.application.use_cases.create_booking import CreateBookingUseCase
from src.domain.entities.booking import Booking, BookingStatus
from src.domain.services.booking_domain_service import BookingDomainService


@pytest.fixture
def user_id():
    return uuid4()


@pytest.fixture
def resource_id():
    return uuid4()


@pytest.fixture
def valid_times():
    now = datetime.utcnow()
    return now + timedelta(hours=1), now + timedelta(hours=3)


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
    use_case, mock_repo, user_id, resource_id, valid_times
):
    start_time, end_time = valid_times

    # Arrange
    expected_booking = Booking(
        user_id=user_id,
        resource_id=resource_id,
        start_time=start_time,
        end_time=end_time,
    )
    mock_repo.save.return_value = expected_booking

    dto = CreateBookingDTO(
        user_id=user_id,
        resource_id=resource_id,
        start_time=start_time,
        end_time=end_time,
    )

    # Act
    result = await use_case.execute(dto)

    # Assert
    assert result.user_id == user_id
    assert result.resource_id == resource_id
    assert result.status == BookingStatus.PENDING
    mock_repo.save.assert_called_once()


@pytest.mark.asyncio
async def test_create_booking_with_schedule_conflict(
    use_case, mock_repo, user_id, resource_id, valid_times
):
    start_time, end_time = valid_times

    # Arrange: an existing booking occupies the same slot
    existing_booking = Booking(
        user_id=user_id,
        resource_id=resource_id,
        start_time=start_time,
        end_time=end_time,
    )
    mock_repo.list_by_user.return_value = [existing_booking]

    dto = CreateBookingDTO(
        user_id=user_id,
        resource_id=resource_id,
        start_time=start_time,
        end_time=end_time,
    )

    # Act & Assert
    with pytest.raises(ValueError, match="schedule conflict"):
        await use_case.execute(dto)

    mock_repo.save.assert_not_called()
