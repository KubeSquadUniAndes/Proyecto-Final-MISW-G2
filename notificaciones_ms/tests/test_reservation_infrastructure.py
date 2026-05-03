"""Infrastructure layer tests for reservation confirmation flow."""
import os
os.environ.setdefault("INTERNAL_API_KEY", "test-key")

from datetime import date
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from httpx import AsyncClient, ASGITransport

from src.application.dtos.reservation_confirmation_dto import (
    ReservationConfirmationDTO,
    ReservationConfirmationResultDTO,
)
from src.infrastructure.http.schemas.reservation_notification_schema import (
    ReservationConfirmationRequest,
    ReservationConfirmationResponse,
)


# ── DTOs ──────────────────────────────────────────────────────────────────────

def test_reservation_confirmation_dto_valid():
    dto = ReservationConfirmationDTO(
        reservation_code=uuid4(),
        guest_name="Ana López",
        guest_email="ana@example.com",
        property_name="Hostal Medellín",
        property_address="Carrera 70 # 44-55",
        check_in=date(2026, 7, 10),
        check_out=date(2026, 7, 15),
        num_guests=1,
        total_amount=450000.0,
        property_contact="+57 4 555 1234",
    )
    assert dto.num_guests == 1
    assert dto.total_amount == 450000.0


def test_reservation_confirmation_result_dto_success():
    dto = ReservationConfirmationResultDTO(email_sent=True, errors=[])
    assert dto.email_sent is True
    assert dto.errors == []


def test_reservation_confirmation_result_dto_failure():
    dto = ReservationConfirmationResultDTO(
        email_sent=False, errors=["email: failed or not configured"]
    )
    assert dto.email_sent is False
    assert len(dto.errors) == 1


# ── Schemas ───────────────────────────────────────────────────────────────────

def test_reservation_confirmation_request_valid():
    r = ReservationConfirmationRequest(
        reservation_code=uuid4(),
        guest_name="Carlos Ruiz",
        guest_email="carlos@example.com",
        property_name="Apart Hotel",
        property_address="Av. El Dorado 100",
        check_in=date(2026, 8, 1),
        check_out=date(2026, 8, 3),
        num_guests=3,
        total_amount=300000.0,
        property_contact="+57 1 800 0000",
    )
    assert r.guest_email == "carlos@example.com"


def test_reservation_confirmation_response_email_sent():
    r = ReservationConfirmationResponse(email_sent=True, errors=[])
    assert r.email_sent is True


def test_reservation_confirmation_response_with_errors():
    r = ReservationConfirmationResponse(
        email_sent=False, errors=["email: failed or not configured"]
    )
    assert r.email_sent is False
    assert len(r.errors) == 1


# ── Email channel ─────────────────────────────────────────────────────────────

@pytest.fixture
def reservation_dto():
    return ReservationConfirmationDTO(
        reservation_code=uuid4(),
        guest_name="Juan Pérez",
        guest_email="juan@example.com",
        property_name="Hotel Bogotá Plaza",
        property_address="Calle 123 # 45-67, Bogotá",
        check_in=date(2026, 6, 1),
        check_out=date(2026, 6, 5),
        num_guests=2,
        total_amount=850000.0,
        property_contact="+57 1 234 5678",
    )


@pytest.mark.asyncio
async def test_reservation_email_not_configured(reservation_dto):
    from src.infrastructure.channels.reservation_email_channel import (
        send_reservation_confirmation_email,
    )
    with patch("src.infrastructure.channels.reservation_email_channel.settings") as mock_settings:
        mock_settings.SMTP_USER = ""
        mock_settings.SMTP_PASSWORD = ""
        result = await send_reservation_confirmation_email(reservation_dto)
    assert result is False


@pytest.mark.asyncio
async def test_reservation_email_smtp_error(reservation_dto):
    from src.infrastructure.channels.reservation_email_channel import (
        send_reservation_confirmation_email,
    )
    with patch("src.infrastructure.channels.reservation_email_channel.settings") as mock_settings, \
         patch("src.infrastructure.channels.reservation_email_channel.smtplib.SMTP") as mock_smtp:
        mock_settings.SMTP_USER = "user@test.com"
        mock_settings.SMTP_PASSWORD = "pass"
        mock_settings.SMTP_HOST = "smtp.test.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.EMAIL_FROM = "from@test.com"
        mock_smtp.side_effect = Exception("SMTP connection error")
        result = await send_reservation_confirmation_email(reservation_dto)
    assert result is False


@pytest.mark.asyncio
async def test_reservation_email_sent_successfully(reservation_dto):
    from src.infrastructure.channels.reservation_email_channel import (
        send_reservation_confirmation_email,
    )
    with patch("src.infrastructure.channels.reservation_email_channel.settings") as mock_settings, \
         patch("src.infrastructure.channels.reservation_email_channel.smtplib.SMTP") as mock_smtp:
        mock_settings.SMTP_USER = "user@test.com"
        mock_settings.SMTP_PASSWORD = "pass"
        mock_settings.SMTP_HOST = "smtp.test.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.EMAIL_FROM = "from@test.com"
        mock_server = mock_smtp.return_value.__enter__.return_value
        result = await send_reservation_confirmation_email(reservation_dto)
    assert result is True
    mock_server.sendmail.assert_called_once()


# ── HTTP Router ───────────────────────────────────────────────────────────────

@pytest.fixture
def app():
    from src.main import create_app
    return create_app()


def _reservation_payload(reservation_dto: ReservationConfirmationDTO) -> dict:
    return {
        "reservation_code": str(reservation_dto.reservation_code),
        "guest_name": reservation_dto.guest_name,
        "guest_email": reservation_dto.guest_email,
        "property_name": reservation_dto.property_name,
        "property_address": reservation_dto.property_address,
        "check_in": reservation_dto.check_in.isoformat(),
        "check_out": reservation_dto.check_out.isoformat(),
        "num_guests": reservation_dto.num_guests,
        "total_amount": reservation_dto.total_amount,
        "property_contact": reservation_dto.property_contact,
    }


@pytest.mark.asyncio
async def test_reservation_confirmation_missing_api_key(app, reservation_dto):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/notifications/reservations/confirmation",
            json=_reservation_payload(reservation_dto),
        )
    assert resp.status_code in (403, 422)


@pytest.mark.asyncio
async def test_reservation_confirmation_wrong_api_key(app, reservation_dto):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/notifications/reservations/confirmation",
            json=_reservation_payload(reservation_dto),
            headers={"x-api-key": "wrong-key"},
        )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_reservation_confirmation_success(app, reservation_dto):
    from src.infrastructure.config.settings import settings as real_settings
    with patch(
        "src.infrastructure.http.routes.reservation_notification_router.SendReservationConfirmationUseCase"
    ) as MockUC:
        mock_uc = AsyncMock()
        mock_uc.execute.return_value = ReservationConfirmationResultDTO(
            email_sent=True, errors=[]
        )
        MockUC.return_value = mock_uc

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/notifications/reservations/confirmation",
                json=_reservation_payload(reservation_dto),
                headers={"x-api-key": real_settings.INTERNAL_API_KEY},
            )
    assert resp.status_code == 200
    body = resp.json()
    assert body["email_sent"] is True
    assert body["errors"] == []


@pytest.mark.asyncio
async def test_reservation_confirmation_email_fails(app, reservation_dto):
    from src.infrastructure.config.settings import settings as real_settings
    with patch(
        "src.infrastructure.http.routes.reservation_notification_router.SendReservationConfirmationUseCase"
    ) as MockUC:
        mock_uc = AsyncMock()
        mock_uc.execute.return_value = ReservationConfirmationResultDTO(
            email_sent=False, errors=["email: failed or not configured"]
        )
        MockUC.return_value = mock_uc

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/notifications/reservations/confirmation",
                json=_reservation_payload(reservation_dto),
                headers={"x-api-key": real_settings.INTERNAL_API_KEY},
            )
    assert resp.status_code == 200
    body = resp.json()
    assert body["email_sent"] is False
    assert body["errors"] == ["email: failed or not configured"]
