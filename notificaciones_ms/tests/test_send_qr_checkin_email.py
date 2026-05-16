"""Tests for QR check-in email use cases and channel functions."""

import base64
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.application.dtos.qr_checkin_email_dto import (
    QrCancelledEmailDTO,
    QrCheckinEmailDTO,
)
from src.application.use_cases.send_qr_checkin_email import (
    SendQrCancelledEmailUseCase,
    SendQrCheckinEmailUseCase,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

# Minimal 10x10 black RGB PNG in base64 (valid PNG bytes for PDF/HTML rendering)
_TINY_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAIAAAACUFjqAAAADUlEQVR4nGNgGAWkAwABNgABVtF/yAAAAABJRU5ErkJggg=="
)


@pytest.fixture
def checkin_dto():
    return QrCheckinEmailDTO(
        reservation_code="TH-2026-QR001",
        guest_name="Ana Torres",
        guest_email="ana@example.com",
        property_name="Hotel Bogotá Plaza",
        property_address="Calle 123 #45-67, Bogotá",
        check_in=date(2026, 6, 10),
        check_out=date(2026, 6, 15),
        room_type="Doble estándar",
        num_guests=2,
        qr_code=_TINY_PNG_B64,
    )


@pytest.fixture
def cancelled_dto():
    return QrCancelledEmailDTO(
        reservation_code="TH-2026-QR001",
        guest_name="Ana Torres",
        guest_email="ana@example.com",
        property_name="Hotel Bogotá Plaza",
        check_in=date(2026, 6, 10),
        check_out=date(2026, 6, 15),
    )


# ── SendQrCheckinEmailUseCase ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_send_qr_checkin_email_success(checkin_dto):
    with patch(
        "src.application.use_cases.send_qr_checkin_email.send_qr_checkin_email",
        new=AsyncMock(return_value=True),
    ):
        result = await SendQrCheckinEmailUseCase().execute(checkin_dto)

    assert result.email_sent is True
    assert result.errors == []


@pytest.mark.asyncio
async def test_send_qr_checkin_email_failure(checkin_dto):
    with patch(
        "src.application.use_cases.send_qr_checkin_email.send_qr_checkin_email",
        new=AsyncMock(return_value=False),
    ):
        result = await SendQrCheckinEmailUseCase().execute(checkin_dto)

    assert result.email_sent is False
    assert len(result.errors) == 1
    assert "email" in result.errors[0]


# ── SendQrCancelledEmailUseCase ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_send_qr_cancelled_email_success(cancelled_dto):
    with patch(
        "src.application.use_cases.send_qr_checkin_email.send_qr_cancelled_email",
        new=AsyncMock(return_value=True),
    ):
        result = await SendQrCancelledEmailUseCase().execute(cancelled_dto)

    assert result.email_sent is True
    assert result.errors == []


@pytest.mark.asyncio
async def test_send_qr_cancelled_email_failure(cancelled_dto):
    with patch(
        "src.application.use_cases.send_qr_checkin_email.send_qr_cancelled_email",
        new=AsyncMock(return_value=False),
    ):
        result = await SendQrCancelledEmailUseCase().execute(cancelled_dto)

    assert result.email_sent is False
    assert len(result.errors) == 1


# ── Channel: HTML builders ────────────────────────────────────────────────────


def test_build_qr_html_contains_reservation_code(checkin_dto):
    from src.infrastructure.channels.qr_checkin_email_channel import _build_qr_html

    html = _build_qr_html(checkin_dto)
    assert "TH-2026-QR001" in html
    assert "Ana Torres" in html
    assert "Hotel Bogotá Plaza" in html
    assert "data:image/png;base64," in html


def test_build_qr_html_contains_dates(checkin_dto):
    from src.infrastructure.channels.qr_checkin_email_channel import _build_qr_html

    html = _build_qr_html(checkin_dto)
    assert "10/06/2026" in html
    assert "15/06/2026" in html


def test_build_cancelled_html_contains_reservation_info(cancelled_dto):
    from src.infrastructure.channels.qr_checkin_email_channel import (
        _build_cancelled_html,
    )

    html = _build_cancelled_html(cancelled_dto)
    assert "TH-2026-QR001" in html
    assert "Ana Torres" in html
    assert "invalidado" in html


def test_build_cancelled_html_contains_dates(cancelled_dto):
    from src.infrastructure.channels.qr_checkin_email_channel import (
        _build_cancelled_html,
    )

    html = _build_cancelled_html(cancelled_dto)
    assert "10/06/2026" in html
    assert "15/06/2026" in html


# ── Channel: PDF builder ──────────────────────────────────────────────────────


def test_build_qr_pdf_returns_bytes(checkin_dto):
    from src.infrastructure.channels.qr_checkin_email_channel import _build_qr_pdf

    pdf_bytes = _build_qr_pdf(checkin_dto)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
    # PDF magic bytes
    assert pdf_bytes[:4] == b"%PDF"


# ── Channel: send_qr_checkin_email (SMTP path) ────────────────────────────────


@pytest.mark.asyncio
async def test_send_qr_checkin_skips_when_smtp_not_configured(checkin_dto):
    with patch(
        "src.infrastructure.channels.qr_checkin_email_channel.settings"
    ) as mock_settings:
        mock_settings.SMTP_USER = ""
        mock_settings.SMTP_PASSWORD = ""
        from src.infrastructure.channels.qr_checkin_email_channel import (
            send_qr_checkin_email,
        )

        result = await send_qr_checkin_email(checkin_dto)

    assert result is False


@pytest.mark.asyncio
async def test_send_qr_checkin_email_smtp_success(checkin_dto):
    mock_server = MagicMock()
    mock_server.__enter__ = MagicMock(return_value=mock_server)
    mock_server.__exit__ = MagicMock(return_value=False)

    with patch(
        "src.infrastructure.channels.qr_checkin_email_channel.settings"
    ) as mock_settings, patch(
        "src.infrastructure.channels.qr_checkin_email_channel.smtplib.SMTP",
        return_value=mock_server,
    ):
        mock_settings.SMTP_USER = "user@example.com"
        mock_settings.SMTP_PASSWORD = "secret"
        mock_settings.SMTP_HOST = "smtp.example.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.EMAIL_FROM = "noreply@travelhub.com"

        from src.infrastructure.channels.qr_checkin_email_channel import (
            send_qr_checkin_email,
        )

        result = await send_qr_checkin_email(checkin_dto)

    assert result is True
    mock_server.sendmail.assert_called_once()


@pytest.mark.asyncio
async def test_send_qr_checkin_email_smtp_error_returns_false(checkin_dto):
    with patch(
        "src.infrastructure.channels.qr_checkin_email_channel.settings"
    ) as mock_settings, patch(
        "src.infrastructure.channels.qr_checkin_email_channel.smtplib.SMTP",
        side_effect=OSError("connection refused"),
    ):
        mock_settings.SMTP_USER = "user@example.com"
        mock_settings.SMTP_PASSWORD = "secret"
        mock_settings.SMTP_HOST = "smtp.example.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.EMAIL_FROM = "noreply@travelhub.com"

        from src.infrastructure.channels.qr_checkin_email_channel import (
            send_qr_checkin_email,
        )

        result = await send_qr_checkin_email(checkin_dto)

    assert result is False


# ── Channel: send_qr_cancelled_email (SMTP path) ─────────────────────────────


@pytest.mark.asyncio
async def test_send_qr_cancelled_skips_when_smtp_not_configured(cancelled_dto):
    with patch(
        "src.infrastructure.channels.qr_checkin_email_channel.settings"
    ) as mock_settings:
        mock_settings.SMTP_USER = ""
        mock_settings.SMTP_PASSWORD = ""
        from src.infrastructure.channels.qr_checkin_email_channel import (
            send_qr_cancelled_email,
        )

        result = await send_qr_cancelled_email(cancelled_dto)

    assert result is False


@pytest.mark.asyncio
async def test_send_qr_cancelled_email_smtp_success(cancelled_dto):
    mock_server = MagicMock()
    mock_server.__enter__ = MagicMock(return_value=mock_server)
    mock_server.__exit__ = MagicMock(return_value=False)

    with patch(
        "src.infrastructure.channels.qr_checkin_email_channel.settings"
    ) as mock_settings, patch(
        "src.infrastructure.channels.qr_checkin_email_channel.smtplib.SMTP",
        return_value=mock_server,
    ):
        mock_settings.SMTP_USER = "user@example.com"
        mock_settings.SMTP_PASSWORD = "secret"
        mock_settings.SMTP_HOST = "smtp.example.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.EMAIL_FROM = "noreply@travelhub.com"

        from src.infrastructure.channels.qr_checkin_email_channel import (
            send_qr_cancelled_email,
        )

        result = await send_qr_cancelled_email(cancelled_dto)

    assert result is True
    mock_server.sendmail.assert_called_once()


@pytest.mark.asyncio
async def test_send_qr_cancelled_email_smtp_error_returns_false(cancelled_dto):
    with patch(
        "src.infrastructure.channels.qr_checkin_email_channel.settings"
    ) as mock_settings, patch(
        "src.infrastructure.channels.qr_checkin_email_channel.smtplib.SMTP",
        side_effect=OSError("connection refused"),
    ):
        mock_settings.SMTP_USER = "user@example.com"
        mock_settings.SMTP_PASSWORD = "secret"
        mock_settings.SMTP_HOST = "smtp.example.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.EMAIL_FROM = "noreply@travelhub.com"

        from src.infrastructure.channels.qr_checkin_email_channel import (
            send_qr_cancelled_email,
        )

        result = await send_qr_cancelled_email(cancelled_dto)

    assert result is False
