import uuid
from datetime import datetime
from typing import Optional

from src.domain.entities.payment import Payment
from src.domain.repositories.payment_repository_port import PaymentRepositoryPort
from src.infrastructure.clients.reservas_client import ReservasClient
from src.infrastructure.clients.notificaciones_client import NotificacionesClient
from src.infrastructure.config.settings import settings


class ConfirmPaymentUseCase:
    def __init__(
        self,
        payment_repository: PaymentRepositoryPort,
        reservas_client: ReservasClient,
        notificaciones_client: NotificacionesClient,
    ):
        self.payment_repository = payment_repository
        self.reservas_client = reservas_client
        self.notificaciones_client = notificaciones_client

    async def execute(
        self,
        booking_id: uuid.UUID,
        provider_transaction_id: str,
        payment_timestamp: Optional[datetime] = None,
    ) -> Payment:
        """
        Confirm payment and update booking status with retry logic.
        
        Criteria:
        - Update payment status to CONFIRMED
        - Store provider transaction ID and timestamp
        - Update booking status to 'confirmed' (with retry)
        - Send confirmation email
        - Complete in < 500ms
        """
        start_time = datetime.utcnow()
        
        # Find payment
        payment = await self.payment_repository.find_by_booking_id(booking_id)
        if not payment:
            raise ValueError(f"Payment for booking {booking_id} not found")

        # Confirm payment
        payment.confirm(
            provider_transaction_id=provider_transaction_id,
            payment_timestamp=payment_timestamp or datetime.utcnow(),
        )
        payment = await self.payment_repository.update(payment)

        # Update booking with retry logic
        success = False
        for attempt in range(settings.MAX_RETRY_ATTEMPTS):
            success = await self.reservas_client.update_booking_status(
                booking_id=booking_id,
                status="confirmed",
                payment_id=payment.id,
            )
            if success:
                break
            payment.increment_retry()
            await self.payment_repository.update(payment)

        if not success:
            # Generate alert for manual review
            print(f"⚠️ ALERT: Failed to update booking {booking_id} after {settings.MAX_RETRY_ATTEMPTS} attempts")
            payment.fail()
            await self.payment_repository.update(payment)
            raise Exception(f"Failed to update booking after {settings.MAX_RETRY_ATTEMPTS} retries")

        # Send confirmation email (fire and forget)
        if payment.cardholder_email:
            await self.notificaciones_client.send_payment_confirmation(
                booking_id=booking_id,
                email=payment.cardholder_email,
                amount=payment.amount,
                currency=payment.currency,
            )

        # Check timing
        elapsed = (datetime.utcnow() - start_time).total_seconds() * 1000
        if elapsed > settings.PAYMENT_TIMEOUT_MS:
            print(f"⚠️ Payment confirmation took {elapsed}ms (target: {settings.PAYMENT_TIMEOUT_MS}ms)")

        return payment
