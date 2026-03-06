"""Tests for SendNotificationUseCase using mocks."""
from datetime import datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from src.application.dtos.notification_dto import SendNotificationDTO
from src.application.use_cases.send_notification import SendNotificationUseCase


@pytest.fixture
def dto():
    return SendNotificationDTO(
        user_id=uuid4(),
        booking_id=uuid4(),
        anomaly_type="random_sample",
        severity="medium",
        score=0.73,
        description="Random sampling triggered anomaly flag",
        detected_at=datetime.utcnow(),
    )


@pytest.mark.asyncio
async def test_both_channels_succeed(dto):
    with patch("src.application.use_cases.send_notification.send_email", new=AsyncMock(return_value=True)), \
         patch("src.application.use_cases.send_notification.send_slack", new=AsyncMock(return_value=True)):
        result = await SendNotificationUseCase().execute(dto)

    assert result.email_sent is True
    assert result.slack_sent is True
    assert result.errors == []


@pytest.mark.asyncio
async def test_email_fails_slack_succeeds(dto):
    with patch("src.application.use_cases.send_notification.send_email", new=AsyncMock(return_value=False)), \
         patch("src.application.use_cases.send_notification.send_slack", new=AsyncMock(return_value=True)):
        result = await SendNotificationUseCase().execute(dto)

    assert result.email_sent is False
    assert result.slack_sent is True
    assert len(result.errors) == 1


@pytest.mark.asyncio
async def test_both_channels_fail(dto):
    with patch("src.application.use_cases.send_notification.send_email", new=AsyncMock(return_value=False)), \
         patch("src.application.use_cases.send_notification.send_slack", new=AsyncMock(return_value=False)):
        result = await SendNotificationUseCase().execute(dto)

    assert result.email_sent is False
    assert result.slack_sent is False
    assert len(result.errors) == 2
