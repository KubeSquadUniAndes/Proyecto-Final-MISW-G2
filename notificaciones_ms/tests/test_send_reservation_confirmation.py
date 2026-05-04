"""Tests for SendReservationConfirmationUseCase using mocks."""
from datetime import date
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from src.application.dtos.reservation_confirmation_dto import ReservationConfirmationDTO
from src.application.use_cases.send_reservation_confirmation import (
    SendReservationConfirmationUseCase,
)


@pytest.fixture
def dto():
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
async def test_email_sent_successfully(dto):
    with patch(
        "src.application.use_cases.send_reservation_confirmation.send_reservation_confirmation_email",
        new=AsyncMock(return_value=True),
    ):
        result = await SendReservationConfirmationUseCase().execute(dto)

    assert result.email_sent is True
    assert result.errors == []


@pytest.mark.asyncio
async def test_email_fails_adds_error(dto):
    with patch(
        "src.application.use_cases.send_reservation_confirmation.send_reservation_confirmation_email",
        new=AsyncMock(return_value=False),
    ):
        result = await SendReservationConfirmationUseCase().execute(dto)

    assert result.email_sent is False
    assert len(result.errors) == 1
    assert result.errors[0] == "email: failed or not configured"
