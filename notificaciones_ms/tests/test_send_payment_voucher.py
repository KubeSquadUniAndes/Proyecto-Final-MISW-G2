"""Tests for SendPaymentVoucherUseCase using mocks."""
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.application.dtos.payment_voucher_dto import PaymentVoucherDTO
from src.application.use_cases.send_payment_voucher import SendPaymentVoucherUseCase


@pytest.fixture
def dto():
    return PaymentVoucherDTO(
        guest_name="Juan Pérez",
        guest_email="juan@example.com",
        reservation_code="TH-2026-00123",
        property_name="Hotel Bogotá Plaza",
        property_address="Calle 123 # 45-67, Bogotá",
        check_in=date(2026, 6, 1),
        check_out=date(2026, 6, 5),
        room_type="Habitación Doble Estándar",
        num_guests=2,
        transaction_id="txn_3PqK2aLkdIwHu7ix0J4M5N6O",
        paid_at=datetime(2026, 5, 9, 14, 32, 10),
        payment_method="Visa •••• 4242",
        nightly_rate=200000.0,
        num_nights=4,
        subtotal=800000.0,
        taxes=152000.0,
        discounts=0.0,
        total_amount=952000.0,
    )


@pytest.mark.asyncio
async def test_email_sent_successfully(dto):
    with patch(
        "src.application.use_cases.send_payment_voucher.send_payment_voucher_email",
        new=AsyncMock(return_value=True),
    ):
        result = await SendPaymentVoucherUseCase().execute(dto)

    assert result.email_sent is True
    assert result.errors == []


@pytest.mark.asyncio
async def test_email_fails_adds_error(dto):
    with patch(
        "src.application.use_cases.send_payment_voucher.send_payment_voucher_email",
        new=AsyncMock(return_value=False),
    ):
        result = await SendPaymentVoucherUseCase().execute(dto)

    assert result.email_sent is False
    assert len(result.errors) == 1
    assert result.errors[0] == "email: failed or not configured"


@pytest.mark.asyncio
async def test_pdf_generation(dto):
    """Verifies that _build_pdf produces non-empty bytes without raising."""
    from src.infrastructure.channels.payment_voucher_email_channel import _build_pdf

    pdf_bytes = _build_pdf(dto)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
    # PDF magic bytes
    assert pdf_bytes[:4] == b"%PDF"


@pytest.mark.asyncio
async def test_html_contains_key_fields(dto):
    from src.infrastructure.channels.payment_voucher_email_channel import _build_html

    html = _build_html(dto)
    assert dto.reservation_code in html
    assert dto.transaction_id in html
    assert dto.guest_name in html
    assert dto.payment_method in html
    assert "952,000.00" in html


@pytest.mark.asyncio
async def test_smtp_not_configured_returns_false(dto):
    with patch(
        "src.infrastructure.channels.payment_voucher_email_channel.settings"
    ) as mock_settings:
        mock_settings.SMTP_USER = ""
        mock_settings.SMTP_PASSWORD = ""
        from src.infrastructure.channels.payment_voucher_email_channel import (
            send_payment_voucher_email,
        )
        result = await send_payment_voucher_email(dto)

    assert result is False


@pytest.mark.asyncio
async def test_smtp_send_failure_returns_false(dto):
    with patch(
        "src.infrastructure.channels.payment_voucher_email_channel.settings"
    ) as mock_settings:
        mock_settings.SMTP_USER = "user@example.com"
        mock_settings.SMTP_PASSWORD = "secret"
        mock_settings.SMTP_HOST = "smtp.gmail.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.EMAIL_FROM = "no-reply@travelhub.com"
        with patch("smtplib.SMTP") as mock_smtp:
            mock_smtp.return_value.__enter__.return_value.sendmail.side_effect = Exception(
                "connection refused"
            )
            from src.infrastructure.channels.payment_voucher_email_channel import (
                send_payment_voucher_email,
            )
            result = await send_payment_voucher_email(dto)

    assert result is False
