"""Tests for anomaly detection use case using mocks."""
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from src.application.dtos.analysis_dto import AnalyzeBookingDTO
from src.application.use_cases.analyze_booking import AnalyzeBookingUseCase
from src.domain.services.anomaly_detector_service import AnomalyDetectorService


@pytest.fixture
def user_id():
    return uuid4()


@pytest.fixture
def booking_id():
    return uuid4()


@pytest.fixture
def resource_id():
    return uuid4()


@pytest.fixture
def valid_dto(user_id, booking_id, resource_id):
    now = datetime.utcnow()
    return AnalyzeBookingDTO(
        user_id=user_id,
        booking_id=booking_id,
        resource_id=resource_id,
        start_time=now + timedelta(hours=1),
        end_time=now + timedelta(hours=2),
    )


@pytest.fixture
def mock_history_repo():
    repo = AsyncMock()
    repo.count_recent_bookings.return_value = 0
    repo.count_distinct_resources.return_value = 0
    return repo


@pytest.fixture
def mock_anomaly_repo():
    repo = AsyncMock()
    repo.save.side_effect = lambda e: e  # return entity as-is
    return repo


@pytest.fixture
def mock_notification():
    notif = AsyncMock()
    notif.block_user.return_value = True
    notif.send_security_alert_email.return_value = True
    return notif


# ── Clean booking (no anomaly) ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_clean_booking_no_anomaly(
    valid_dto, mock_history_repo, mock_anomaly_repo, mock_notification
):
    detector = AnomalyDetectorService(mock_history_repo, random_anomaly_rate=0.0)
    use_case = AnalyzeBookingUseCase(detector, mock_anomaly_repo, mock_notification)

    result = await use_case.execute(valid_dto)

    assert result.is_anomalous is False
    assert result.anomaly_count == 0
    assert result.action_taken == "none"
    mock_notification.block_user.assert_not_called()
    mock_notification.send_security_alert_email.assert_not_called()


# ── Random anomaly always triggers (rate=1.0) ─────────────────────────────────

@pytest.mark.asyncio
async def test_random_anomaly_always_triggers(
    valid_dto, mock_history_repo, mock_anomaly_repo, mock_notification
):
    detector = AnomalyDetectorService(mock_history_repo, random_anomaly_rate=1.0)
    use_case = AnalyzeBookingUseCase(detector, mock_anomaly_repo, mock_notification)

    result = await use_case.execute(valid_dto)

    assert result.is_anomalous is True
    assert result.anomaly_count >= 1
    mock_notification.block_user.assert_called_once_with(
        valid_dto.user_id, pytest.approx(result.events[0].description, rel=1e-3)
    )


# ── High frequency heuristic ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_high_frequency_triggers_anomaly(
    valid_dto, mock_history_repo, mock_anomaly_repo, mock_notification
):
    mock_history_repo.count_recent_bookings.return_value = 10  # above threshold=5
    detector = AnomalyDetectorService(mock_history_repo, random_anomaly_rate=0.0)
    use_case = AnalyzeBookingUseCase(detector, mock_anomaly_repo, mock_notification)

    result = await use_case.execute(valid_dto)

    assert result.is_anomalous is True
    assert any(e.anomaly_type.value == "high_frequency" for e in result.events)
    mock_notification.block_user.assert_called_once()


# ── Unusual duration heuristic ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_short_duration_triggers_anomaly(
    user_id, booking_id, resource_id, mock_history_repo, mock_anomaly_repo, mock_notification
):
    now = datetime.utcnow()
    dto = AnalyzeBookingDTO(
        user_id=user_id,
        booking_id=booking_id,
        resource_id=resource_id,
        start_time=now + timedelta(hours=1),
        end_time=now + timedelta(hours=1, minutes=5),  # only 5 min, below 15 min threshold
    )
    detector = AnomalyDetectorService(mock_history_repo, random_anomaly_rate=0.0)
    use_case = AnalyzeBookingUseCase(detector, mock_anomaly_repo, mock_notification)

    result = await use_case.execute(dto)

    assert result.is_anomalous is True
    assert any(e.anomaly_type.value == "unusual_duration" for e in result.events)
