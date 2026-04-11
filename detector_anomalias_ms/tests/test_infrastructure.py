"""Infrastructure layer tests for detector_anomalias_ms."""
import os
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://x:x@localhost/x")

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from src.infrastructure.config.settings import Settings
from src.infrastructure.http.dependencies import require_internal_api_key
from src.infrastructure.http.schemas.analysis_schema import (
    AnalyzeBookingRequest,
    AnalysisResultResponse,
    AnomalyEventResponse,
    ErrorResponse,
)
from src.domain.entities.anomaly_event import AnomalyType, AnomalySeverity
from src.domain.entities.anomaly_event import AnomalyEvent


# ── Settings ──────────────────────────────────────────────────────────────────

def test_settings_defaults():
    s = Settings(DATABASE_URL="postgresql+asyncpg://x:x@localhost/x")
    assert s.APP_NAME == "detector_anomalias_ms"
    assert s.MAX_BOOKINGS_PER_WINDOW > 0
    assert 0.0 <= s.RANDOM_ANOMALY_RATE <= 1.0
    assert s.MIN_DURATION_MINUTES > 0


def test_settings_env_override():
    s = Settings(DATABASE_URL="postgresql+asyncpg://x:x@localhost/x", DEBUG=True, PORT=9999)
    assert s.DEBUG is True
    assert s.PORT == 9999


# ── Schemas ───────────────────────────────────────────────────────────────────

def test_analyze_booking_request_valid():
    now = datetime.utcnow()
    req = AnalyzeBookingRequest(
        user_id=uuid4(),
        booking_id=uuid4(),
        resource_id=uuid4(),
        start_time=now,
        end_time=now + timedelta(hours=1),
    )
    assert req.end_time > req.start_time


def test_analyze_booking_request_invalid_end_before_start():
    now = datetime.utcnow()
    with pytest.raises(Exception):
        AnalyzeBookingRequest(
            user_id=uuid4(),
            booking_id=uuid4(),
            resource_id=uuid4(),
            start_time=now + timedelta(hours=1),
            end_time=now,
        )


def test_error_response_schema():
    e = ErrorResponse(detail="something went wrong")
    assert e.detail == "something went wrong"
    assert e.code is None


def test_analysis_result_response_schema():
    bid = uuid4()
    r = AnalysisResultResponse(
        booking_id=bid,
        is_anomalous=False,
        anomaly_count=0,
        events=[],
        action_taken="none",
        message="ok",
    )
    assert r.booking_id == bid
    assert r.is_anomalous is False


# ── AnomalyEvent entity ───────────────────────────────────────────────────────

def test_anomaly_event_is_high_risk_by_severity():
    e = AnomalyEvent(
        user_id=uuid4(), booking_id=uuid4(),
        anomaly_type=AnomalyType.HIGH_FREQUENCY,
        severity=AnomalySeverity.HIGH,
        score=0.5, description="test",
    )
    assert e.is_high_risk() is True


def test_anomaly_event_is_high_risk_by_score():
    e = AnomalyEvent(
        user_id=uuid4(), booking_id=uuid4(),
        anomaly_type=AnomalyType.RANDOM_SAMPLE,
        severity=AnomalySeverity.LOW,
        score=0.9, description="test",
    )
    assert e.is_high_risk() is True


def test_anomaly_event_not_high_risk():
    e = AnomalyEvent(
        user_id=uuid4(), booking_id=uuid4(),
        anomaly_type=AnomalyType.UNUSUAL_DURATION,
        severity=AnomalySeverity.LOW,
        score=0.3, description="test",
    )
    assert e.is_high_risk() is False


def test_anomaly_event_resolve():
    e = AnomalyEvent(
        user_id=uuid4(), booking_id=uuid4(),
        anomaly_type=AnomalyType.MULTI_RESOURCE,
        severity=AnomalySeverity.MEDIUM,
        score=0.5, description="test",
    )
    assert e.resolved is False
    e.resolve()
    assert e.resolved is True


# ── HTTP Router (mocked DB + use case) ───────────────────────────────────────

def _make_app():
    """Create app with mocked DB engine to avoid real DB connection."""
    with patch("src.infrastructure.database.base.create_async_engine") as mock_engine, \
         patch("src.infrastructure.database.base.async_sessionmaker"):
        mock_engine.return_value = MagicMock()
        from src.main import create_app
        return create_app()


@pytest.fixture
def app():
    return _make_app()


@pytest.mark.asyncio
async def test_health_endpoint(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_analyze_booking_missing_api_key(app):
    now = datetime.utcnow()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/v1/analysis/booking", json={
            "user_id": str(uuid4()),
            "booking_id": str(uuid4()),
            "resource_id": str(uuid4()),
            "start_time": now.isoformat(),
            "end_time": (now + timedelta(hours=1)).isoformat(),
        })
    assert resp.status_code in (403, 422)  # 403 missing key, 422 validation


@pytest.mark.asyncio
async def test_analyze_booking_wrong_api_key(app):
    now = datetime.utcnow()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/analysis/booking",
            json={
                "user_id": str(uuid4()),
                "booking_id": str(uuid4()),
                "resource_id": str(uuid4()),
                "start_time": now.isoformat(),
                "end_time": (now + timedelta(hours=1)).isoformat(),
            },
            headers={"x-api-key": "definitely-wrong-key"},
        )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_analyze_booking_success(app):
    from src.application.dtos.analysis_dto import AnalysisResultDTO
    from src.infrastructure.config.settings import settings as real_settings
    now = datetime.utcnow()
    mock_result = AnalysisResultDTO(
        booking_id=uuid4(),
        is_anomalous=False,
        anomaly_count=0,
        events=[],
        action_taken="none",
        message="ok",
    )
    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("src.infrastructure.database.base.AsyncSessionLocal", return_value=mock_session), \
         patch("src.infrastructure.http.routes.analysis_router._build_use_case") as mock_build:
        mock_uc = AsyncMock()
        mock_uc.execute.return_value = mock_result
        mock_build.return_value = mock_uc

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/analysis/booking",
                json={
                    "user_id": str(uuid4()),
                    "booking_id": str(uuid4()),
                    "resource_id": str(uuid4()),
                    "start_time": now.isoformat(),
                    "end_time": (now + timedelta(hours=1)).isoformat(),
                },
                headers={"x-api-key": real_settings.INTERNAL_API_KEY},
            )
    assert resp.status_code == 200
    assert resp.json()["is_anomalous"] is False


# ── SQLAlchemy Repository ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_anomaly_repo_save():
    from src.infrastructure.database.repositories.sqlalchemy_anomaly_repository import (
        SQLAlchemyAnomalyEventRepository,
    )
    event = AnomalyEvent(
        user_id=uuid4(), booking_id=uuid4(),
        anomaly_type=AnomalyType.RANDOM_SAMPLE,
        severity=AnomalySeverity.MEDIUM,
        score=0.7, description="test",
    )
    mock_session = AsyncMock()
    mock_model = MagicMock()
    mock_model.id = event.id
    mock_model.user_id = event.user_id
    mock_model.booking_id = event.booking_id
    mock_model.anomaly_type = event.anomaly_type
    mock_model.severity = event.severity
    mock_model.score = event.score
    mock_model.description = event.description
    mock_model.resolved = False
    mock_model.created_at = event.created_at
    mock_session.refresh = AsyncMock(side_effect=lambda m: None)

    repo = SQLAlchemyAnomalyEventRepository(mock_session)
    with patch.object(repo, "_to_domain", return_value=event):
        result = await repo.save(event)
    assert result == event
    mock_session.add.assert_called_once()
    mock_session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_anomaly_repo_list_by_user():
    from src.infrastructure.database.repositories.sqlalchemy_anomaly_repository import (
        SQLAlchemyAnomalyEventRepository,
    )
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute = AsyncMock(return_value=mock_result)

    repo = SQLAlchemyAnomalyEventRepository(mock_session)
    result = await repo.list_by_user(uuid4())
    assert result == []


@pytest.mark.asyncio
async def test_anomaly_repo_count_recent():
    from src.infrastructure.database.repositories.sqlalchemy_anomaly_repository import (
        SQLAlchemyAnomalyEventRepository,
    )
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one.return_value = 3
    mock_session.execute = AsyncMock(return_value=mock_result)

    repo = SQLAlchemyAnomalyEventRepository(mock_session)
    count = await repo.count_recent_by_user(uuid4(), datetime.utcnow())
    assert count == 3


# ── Multi-resource anomaly ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_multi_resource_triggers_anomaly():
    from src.domain.services.anomaly_detector_service import AnomalyDetectorService
    from src.domain.entities.booking_analysis import BookingAnalysisRequest

    mock_history = AsyncMock()
    mock_history.count_recent_bookings.return_value = 0
    mock_history.count_distinct_resources.return_value = 10  # above threshold=4

    detector = AnomalyDetectorService(mock_history, random_anomaly_rate=0.0)
    now = datetime.utcnow()
    request = BookingAnalysisRequest(
        user_id=uuid4(), booking_id=uuid4(), resource_id=uuid4(),
        start_time=now + timedelta(hours=1),
        end_time=now + timedelta(hours=2),
    )
    events = await detector.analyze(request)
    assert any(e.anomaly_type == AnomalyType.MULTI_RESOURCE for e in events)


@pytest.mark.asyncio
async def test_long_duration_triggers_anomaly():
    from src.domain.services.anomaly_detector_service import AnomalyDetectorService
    from src.domain.entities.booking_analysis import BookingAnalysisRequest

    mock_history = AsyncMock()
    mock_history.count_recent_bookings.return_value = 0
    mock_history.count_distinct_resources.return_value = 0

    detector = AnomalyDetectorService(mock_history, random_anomaly_rate=0.0)
    now = datetime.utcnow()
    request = BookingAnalysisRequest(
        user_id=uuid4(), booking_id=uuid4(), resource_id=uuid4(),
        start_time=now,
        end_time=now + timedelta(hours=20),  # way above 480 min
    )
    events = await detector.analyze(request)
    assert any(e.anomaly_type == AnomalyType.UNUSUAL_DURATION for e in events)
