"""Infrastructure layer tests for notificaciones_ms."""
import os
os.environ.setdefault("INTERNAL_API_KEY", "test-key")

from datetime import datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from httpx import AsyncClient, ASGITransport

from src.infrastructure.config.settings import Settings
from src.infrastructure.http.schemas.notification_schema import (
    SendNotificationRequest,
    NotificationResultResponse,
    ErrorResponse,
)
from src.application.dtos.notification_dto import SendNotificationDTO, NotificationResultDTO


# ── Settings ──────────────────────────────────────────────────────────────────

def test_settings_defaults():
    s = Settings()
    assert s.APP_NAME == "notificaciones_ms"
    assert s.SMTP_PORT == 587


def test_settings_override():
    s = Settings(DEBUG=True, PORT=9000)
    assert s.DEBUG is True
    assert s.PORT == 9000


# ── Schemas ───────────────────────────────────────────────────────────────────

def test_send_notification_request_valid():
    r = SendNotificationRequest(
        user_id=uuid4(),
        booking_id=uuid4(),
        anomaly_type="random_sample",
        severity="medium",
        score=0.73,
        description="test",
        detected_at=datetime.utcnow(),
    )
    assert r.score == 0.73


def test_notification_result_response():
    r = NotificationResultResponse(email_sent=True, slack_sent=False, errors=["slack: failed"])
    assert r.email_sent is True
    assert len(r.errors) == 1


def test_error_response():
    e = ErrorResponse(detail="forbidden")
    assert e.detail == "forbidden"


# ── DTOs ──────────────────────────────────────────────────────────────────────

def test_notification_result_dto():
    dto = NotificationResultDTO(email_sent=True, slack_sent=True, errors=[])
    assert dto.email_sent is True
    assert dto.errors == []


# ── Email channel ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_send_email_not_configured():
    from src.infrastructure.channels.email_channel import send_email
    dto = SendNotificationDTO(
        user_id=uuid4(), booking_id=uuid4(),
        anomaly_type="random_sample", severity="medium",
        score=0.5, description="test", detected_at=datetime.utcnow(),
    )
    with patch("src.infrastructure.channels.email_channel.settings") as mock_settings:
        mock_settings.SMTP_USER = ""
        mock_settings.SMTP_PASSWORD = ""
        result = await send_email(dto)
    assert result is False


@pytest.mark.asyncio
async def test_send_email_smtp_error():
    from src.infrastructure.channels.email_channel import send_email
    dto = SendNotificationDTO(
        user_id=uuid4(), booking_id=uuid4(),
        anomaly_type="random_sample", severity="medium",
        score=0.5, description="test", detected_at=datetime.utcnow(),
    )
    with patch("src.infrastructure.channels.email_channel.settings") as mock_settings, \
         patch("src.infrastructure.channels.email_channel.smtplib.SMTP") as mock_smtp:
        mock_settings.SMTP_USER = "user@test.com"
        mock_settings.SMTP_PASSWORD = "pass"
        mock_settings.SMTP_HOST = "smtp.test.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.EMAIL_FROM = "from@test.com"
        mock_settings.EMAIL_TO = "to@test.com"
        mock_smtp.side_effect = Exception("SMTP error")
        result = await send_email(dto)
    assert result is False


# ── Slack channel ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_send_slack_not_configured():
    from src.infrastructure.channels.slack_channel import send_slack
    dto = SendNotificationDTO(
        user_id=uuid4(), booking_id=uuid4(),
        anomaly_type="random_sample", severity="medium",
        score=0.5, description="test", detected_at=datetime.utcnow(),
    )
    with patch("src.infrastructure.channels.slack_channel.settings") as mock_settings:
        mock_settings.SLACK_WEBHOOK_URL = ""
        result = await send_slack(dto)
    assert result is False


@pytest.mark.asyncio
async def test_send_slack_http_error():
    from src.infrastructure.channels.slack_channel import send_slack
    dto = SendNotificationDTO(
        user_id=uuid4(), booking_id=uuid4(),
        anomaly_type="random_sample", severity="medium",
        score=0.5, description="test", detected_at=datetime.utcnow(),
    )
    with patch("src.infrastructure.channels.slack_channel.settings") as mock_settings, \
         patch("src.infrastructure.channels.slack_channel.httpx") as mock_httpx:
        mock_settings.SLACK_WEBHOOK_URL = "https://hooks.slack.com/test"
        mock_settings.SLACK_CHANNEL = "#alerts"
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post.side_effect = Exception("HTTP error")
        mock_httpx.AsyncClient.return_value = mock_client
        result = await send_slack(dto)
    assert result is False


# ── HTTP Router ───────────────────────────────────────────────────────────────

@pytest.fixture
def app():
    from src.main import create_app
    return create_app()


@pytest.mark.asyncio
async def test_health_endpoint(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_send_alert_missing_api_key(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/v1/notifications/alert", json={
            "user_id": str(uuid4()),
            "booking_id": str(uuid4()),
            "anomaly_type": "random_sample",
            "severity": "medium",
            "score": 0.7,
            "description": "test",
            "detected_at": datetime.utcnow().isoformat(),
        })
    assert resp.status_code in (403, 422)


@pytest.mark.asyncio
async def test_send_alert_wrong_api_key(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/notifications/alert",
            json={
                "user_id": str(uuid4()),
                "booking_id": str(uuid4()),
                "anomaly_type": "random_sample",
                "severity": "medium",
                "score": 0.7,
                "description": "test",
                "detected_at": datetime.utcnow().isoformat(),
            },
            headers={"x-api-key": "definitely-wrong-key"},
        )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_send_alert_success(app):
    from src.infrastructure.config.settings import settings as real_settings
    with patch("src.infrastructure.http.routes.notification_router.SendNotificationUseCase") as MockUC:
        mock_uc = AsyncMock()
        mock_uc.execute.return_value = NotificationResultDTO(
            email_sent=False, slack_sent=False, errors=["not configured"]
        )
        MockUC.return_value = mock_uc

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/notifications/alert",
                json={
                    "user_id": str(uuid4()),
                    "booking_id": str(uuid4()),
                    "anomaly_type": "random_sample",
                    "severity": "medium",
                    "score": 0.7,
                    "description": "test",
                    "detected_at": datetime.utcnow().isoformat(),
                },
                headers={"x-api-key": real_settings.INTERNAL_API_KEY},
            )
    assert resp.status_code == 200
