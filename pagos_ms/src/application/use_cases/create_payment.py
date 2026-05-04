import uuid
from typing import Optional

from src.domain.entities.payment import Payment, PaymentProvider, PaymentMethod
from src.domain.repositories.payment_repository_port import PaymentRepositoryPort


class CreatePaymentUseCase:
    def __init__(self, payment_repository: PaymentRepositoryPort):
        self.payment_repository = payment_repository

    async def execute(
        self,
        booking_id: uuid.UUID,
        amount: float,
        currency: str,
        payment_provider: PaymentProvider,
        payment_method: PaymentMethod,
        card_last_four: Optional[str] = None,
        cardholder_name: Optional[str] = None,
        cardholder_email: Optional[str] = None,
    ) -> Payment:
        """Create a new payment record"""
        # Check if payment already exists
        existing = await self.payment_repository.find_by_booking_id(booking_id)
        if existing:
            raise ValueError(f"Payment for booking {booking_id} already exists")

        payment = Payment(
            booking_id=booking_id,
            amount=amount,
            currency=currency,
            payment_provider=payment_provider,
            payment_method=payment_method,
            card_last_four=card_last_four,
            cardholder_name=cardholder_name,
            cardholder_email=cardholder_email,
        )

        return await self.payment_repository.save(payment)
