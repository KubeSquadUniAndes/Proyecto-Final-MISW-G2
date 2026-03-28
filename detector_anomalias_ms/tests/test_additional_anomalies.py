"""Additional tests for anomaly detector: multi-resource, long duration, entity methods."""
from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from src.application.dtos.analysis_dto import AnalyzeBookingDTO
from src.application.use_cases.analyze_booking import AnalyzeBookingUseCase
from src.domain.entities.anomaly_event import AnomalyEvent, AnomalyType, AnomalySeverity
from src.domain.services.anomaly_detector_service import AnomalyDetectorService
from unittest.mock import AsyncMock


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
def mock_history_repo():
    repo = AsyncMock()
    repo.count_recent_bookings.return_value = 0
    repo.count_distinct_resources.return_value = 0
    return repo


@pytest.fixture
def mock_anomaly_repo():
    repo = AsyncMock()
    repo.save.side_effect = lambda e: e
    return repo


@pytest.fixture
def mock_notification():
    notif = AsyncMock()
    notif.block_user.return_value = True
    notif.send_security_alert_email.return_value = True
    return notif


# ── Multi-resource anomaly ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_multi_resource_triggers_anomaly(
    user_id, booking_id, resource_id, mock_history_repo, mock_anomaly_repo, mock_notification
):
    mock_history_repo.count_distinct_resources.return_value = 5  # above threshold=4
    now = datetime.utcnow()
    dto = AnalyzeBookingDTO(
        user_id=user_id, booking_id=booking_id, resource_id=resource_id,
        start_time=now + timedelta(hours=1), end_time=now + timedelta(hours=2),
    )
    detector = AnomalyDetectorService(mock_history_repo, random_anomaly_rate=0.0)
    result = await AnalyzeBookingUseCase(detector, mock_anomaly_repo, mock_notification).execute(dto)

    assert result.is_anomalous is True
    assert any(e.anomaly_type.value == "multi_resource" for e in result.events)


# ── Long duration anomaly ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_long_duration_triggers_anomaly(
    user_id, booking_id, resource_id, mock_history_repo, mock_anomaly_repo, mock_notification
):
    now = datetime.utcnow()
    dto = AnalyzeBookingDTO(
        user_id=user_id, booking_id=booking_id, resource_id=resource_id,
        start_time=now + timedelta(hours=1),
        end_time=now + timedelta(hours=1, minutes=600),  # 600 min > 480 max
    )
    detector = AnomalyDetectorService(mock_history_repo, random_anomaly_rate=0.0)
    result = await AnalyzeBookingUseCase(detector, mock_anomaly_repo, mock_notification).execute(dto)

    assert result.is_anomalous is True
    assert any(e.anomaly_type.value == "unusual_duration" for e in result.events)


# ── Multiple anomalies at once ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_multiple_anomalies_detected(
    user_id, booking_id, resource_id, mock_history_repo, mock_anomaly_repo, mock_notification
):
    mock_history_repo.count_recent_bookings.return_value = 10
    mock_history_repo.count_distinct_resources.return_value = 5
    now = datetime.utcnow()
    dto = AnalyzeBookingDTO(
        user_id=user_id, booking_id=booking_id, resource_id=resource_id,
        start_time=now + timedelta(hours=1), end_time=now + timedelta(hours=1, minutes=5),
    )
    detector = AnomalyDetectorService(mock_history_repo, random_anomaly_rate=0.0)
    result = await AnalyzeBookingUseCase(detector, mock_anomaly_repo, mock_notification).execute(dto)

    assert result.anomaly_count >= 3


# ── AnomalyEvent entity ───────────────────────────────────────────────────────

def test_anomaly_event_is_high_risk_by_severity():
    event = AnomalyEvent(
        user_id=uuid4(), booking_id=uuid4(),
        anomaly_type=AnomalyType.HIGH_FREQUENCY,
        severity=AnomalySeverity.HIGH,
        score=0.5,
        description="test",
    )
    assert event.is_high_risk() is True


def test_anomaly_event_is_high_risk_by_score():
    event = AnomalyEvent(
        user_id=uuid4(), booking_id=uuid4(),
        anomaly_type=AnomalyType.RANDOM_SAMPLE,
        severity=AnomalySeverity.LOW,
        score=0.85,
        description="test",
    )
    assert event.is_high_risk() is True


def test_anomaly_event_not_high_risk():
    event = AnomalyEvent(
        user_id=uuid4(), booking_id=uuid4(),
        anomaly_type=AnomalyType.UNUSUAL_DURATION,
        severity=AnomalySeverity.LOW,
        score=0.3,
        description="test",
    )
    assert event.is_high_risk() is False


def test_anomaly_event_resolve():
    event = AnomalyEvent(
        user_id=uuid4(), booking_id=uuid4(),
        anomaly_type=AnomalyType.MULTI_RESOURCE,
        severity=AnomalySeverity.MEDIUM,
        score=0.5,
        description="test",
    )
    assert event.resolved is False
    event.resolve()
    assert event.resolved is True
