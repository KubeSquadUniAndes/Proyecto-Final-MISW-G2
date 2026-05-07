"""Tests for SendBookingNotificationUseCase and FCM channel."""

import os

os.environ.setdefault("INTERNAL_API_KEY", "test-key")

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from src.application.dtos.notification_dto import (
    BookingNotificationDTO,
    BookingNotificationResultDTO,
)


@pytest.fixture
def booking_dto():
    return BookingNotificationDTO(
        fcm_token="fake-fcm-token-123",
        booking_id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        booking_code="TH-2026-ABCDE",
        hotel_name="Hotel Cartagena",
        check_in="2026-06-01",
        check_out="2026-06-05",
        status="Pendiente de pago",
        event_type="created",
    )


# ── Use Case ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_booking_notification_fcm_success(booking_dto):
    from src.application.use_cases.send_booking_notification import (
        SendBookingNotificationUseCase,
    )

    with patch(
        "src.application.use_cases.send_booking_notification.send_fcm",
        new=AsyncMock(return_value=True),
    ):
        result = await SendBookingNotificationUseCase().execute(booking_dto)

    assert result.fcm_sent is True
    assert result.errors == []


@pytest.mark.asyncio
async def test_booking_notification_fcm_fails(booking_dto):
    from src.application.use_cases.send_booking_notification import (
        SendBookingNotificationUseCase,
    )

    with patch(
        "src.application.use_cases.send_booking_notification.send_fcm",
        new=AsyncMock(return_value=False),
    ):
        result = await SendBookingNotificationUseCase().execute(booking_dto)

    assert result.fcm_sent is False
    assert len(result.errors) == 1
    assert "fcm" in result.errors[0]


@pytest.mark.asyncio
async def test_booking_notification_status_changed():
    from src.application.use_cases.send_booking_notification import (
        SendBookingNotificationUseCase,
    )

    dto = BookingNotificationDTO(
        fcm_token="token",
        booking_id="id",
        booking_code="TH-2026-XYZ",
        hotel_name="Hotel Test",
        check_in="2026-06-01",
        check_out="2026-06-05",
        status="Aprobada",
        event_type="status_changed",
    )
    with patch(
        "src.application.use_cases.send_booking_notification.send_fcm",
        new=AsyncMock(return_value=True),
    ):
        result = await SendBookingNotificationUseCase().execute(dto)

    assert result.fcm_sent is True


@pytest.mark.asyncio
async def test_booking_notification_modified():
    from src.application.use_cases.send_booking_notification import (
        SendBookingNotificationUseCase,
    )

    dto = BookingNotificationDTO(
        fcm_token="token",
        booking_id="id",
        booking_code="TH-2026-XYZ",
        hotel_name="Hotel Test",
        check_in="2026-06-01",
        check_out="2026-06-05",
        status="Pendiente",
        event_type="modified",
        change_summary="Fechas actualizadas",
    )
    with patch(
        "src.application.use_cases.send_booking_notification.send_fcm",
        new=AsyncMock(return_value=True),
    ):
        result = await SendBookingNotificationUseCase().execute(dto)

    assert result.fcm_sent is True


# ── FCM Channel ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_fcm_skipped_no_token():
    from src.infrastructure.channels.fcm_channel import send_fcm

    result = await send_fcm("", "title", "body")
    assert result is False


@pytest.mark.asyncio
async def test_fcm_not_configured():
    from src.infrastructure.channels.fcm_channel import send_fcm

    with patch(
        "src.infrastructure.channels.fcm_channel._init_firebase", return_value=False
    ):
        result = await send_fcm("some-token", "title", "body")
    assert result is False


# ── HTTP Router ───────────────────────────────────────────────────────────────


@pytest.fixture
def app():
    from src.main import create_app

    return create_app()


@pytest.mark.asyncio
async def test_booking_notification_endpoint_missing_api_key(app, booking_dto):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/api/v1/notifications/booking",
            json=booking_dto.model_dump(),
        )
    assert resp.status_code in (403, 422)


@pytest.mark.asyncio
async def test_booking_notification_endpoint_wrong_api_key(app, booking_dto):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/api/v1/notifications/booking",
            json=booking_dto.model_dump(),
            headers={"x-api-key": "wrong-key"},
        )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_booking_notification_endpoint_success(app, booking_dto):
    from src.infrastructure.config.settings import settings as real_settings

    with patch(
        "src.infrastructure.http.routes.notification_router.SendBookingNotificationUseCase"
    ) as MockUC:
        mock_uc = AsyncMock()
        mock_uc.execute.return_value = BookingNotificationResultDTO(
            fcm_sent=True, errors=[]
        )
        MockUC.return_value = mock_uc

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post(
                "/api/v1/notifications/booking",
                json=booking_dto.model_dump(),
                headers={"x-api-key": real_settings.INTERNAL_API_KEY},
            )
    assert resp.status_code == 200
    body = resp.json()
    assert body["fcm_sent"] is True
    assert body["errors"] == []
