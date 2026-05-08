import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.use_cases.confirm_payment import ConfirmPaymentUseCase
from src.domain.entities.payment import Payment, PaymentStatus, PaymentProvider, PaymentMethod


@pytest.mark.asyncio
async def test_confirm_payment_success():
    # Arrange
    booking_id = uuid.uuid4()
    payment = Payment(
        id=uuid.uuid4(),
        booking_id=booking_id,
        amount=150.00,
        currency="USD",
        payment_provider=PaymentProvider.STRIPE,
        payment_method=PaymentMethod.CREDIT_CARD,
        status=PaymentStatus.PENDING,
        cardholder_email="test@example.com",
    )

    mock_repository = AsyncMock()
    mock_repository.find_by_booking_id.return_value = payment
    mock_repository.update.return_value = payment

    mock_reservas_client = AsyncMock()
    mock_reservas_client.update_booking_status.return_value = True

    mock_notificaciones_client = AsyncMock()
    mock_notificaciones_client.send_payment_confirmation.return_value = True

    use_case = ConfirmPaymentUseCase(
        mock_repository, mock_reservas_client, mock_notificaciones_client
    )

    # Act
    result = await use_case.execute(
        booking_id=booking_id,
        provider_transaction_id="ch_1234567890",
        payment_timestamp=datetime.utcnow(),
    )

    # Assert
    assert result.status == PaymentStatus.CONFIRMED
    assert result.provider_transaction_id == "ch_1234567890"
    mock_reservas_client.update_booking_status.assert_called_once()
    mock_notificaciones_client.send_payment_confirmation.assert_called_once()


@pytest.mark.asyncio
async def test_confirm_payment_retry_logic():
    # Arrange
    booking_id = uuid.uuid4()
    payment = Payment(
        id=uuid.uuid4(),
        booking_id=booking_id,
        amount=150.00,
        currency="USD",
        payment_provider=PaymentProvider.STRIPE,
        payment_method=PaymentMethod.CREDIT_CARD,
        status=PaymentStatus.PENDING,
    )

    mock_repository = AsyncMock()
    mock_repository.find_by_booking_id.return_value = payment
    mock_repository.update.return_value = payment

    mock_reservas_client = AsyncMock()
    # Fail first 2 attempts, succeed on 3rd
    mock_reservas_client.update_booking_status.side_effect = [False, False, True]

    mock_notificaciones_client = AsyncMock()

    use_case = ConfirmPaymentUseCase(
        mock_repository, mock_reservas_client, mock_notificaciones_client
    )

    # Act
    result = await use_case.execute(
        booking_id=booking_id,
        provider_transaction_id="ch_1234567890",
    )

    # Assert
    assert result.status == PaymentStatus.CONFIRMED
    assert mock_reservas_client.update_booking_status.call_count == 3
    assert result.retry_count == 2


@pytest.mark.asyncio
async def test_confirm_payment_max_retries_exceeded():
    # Arrange
    booking_id = uuid.uuid4()
    payment = Payment(
        id=uuid.uuid4(),
        booking_id=booking_id,
        amount=150.00,
        currency="USD",
        payment_provider=PaymentProvider.STRIPE,
        payment_method=PaymentMethod.CREDIT_CARD,
        status=PaymentStatus.PENDING,
    )

    mock_repository = AsyncMock()
    mock_repository.find_by_booking_id.return_value = payment
    mock_repository.update.return_value = payment

    mock_reservas_client = AsyncMock()
    mock_reservas_client.update_booking_status.return_value = False

    mock_notificaciones_client = AsyncMock()

    use_case = ConfirmPaymentUseCase(
        mock_repository, mock_reservas_client, mock_notificaciones_client
    )

    # Act & Assert
    with pytest.raises(Exception, match="Failed to update booking after 3 retries"):
        await use_case.execute(
            booking_id=booking_id,
            provider_transaction_id="ch_1234567890",
        )
