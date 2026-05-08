from typing import Optional
import uuid

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.payment import Payment, PaymentStatus, PaymentProvider, PaymentMethod
from src.domain.repositories.payment_repository_port import PaymentRepositoryPort
from src.infrastructure.database.models.payment_model import PaymentModel
from src.infrastructure.config.settings import settings


class PaymentRepository(PaymentRepositoryPort):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _to_entity(self, model: PaymentModel) -> Payment:
        cardholder_name = None
        cardholder_email = None

        if model.cardholder_name:
            result = await self.session.execute(
                text(
                    "SELECT pgp_sym_decrypt(:data, :key) AS decrypted"
                ),
                {"data": bytes(model.cardholder_name), "key": settings.AES_ENCRYPTION_KEY},
            )
            row = result.fetchone()
            if row:
                decrypted = row[0]
                cardholder_name = decrypted if isinstance(decrypted, str) else decrypted.decode("utf-8")

        if model.cardholder_email:
            result = await self.session.execute(
                text(
                    "SELECT pgp_sym_decrypt(:data, :key) AS decrypted"
                ),
                {"data": bytes(model.cardholder_email), "key": settings.AES_ENCRYPTION_KEY},
            )
            row = result.fetchone()
            if row:
                decrypted = row[0]
                cardholder_email = decrypted if isinstance(decrypted, str) else decrypted.decode("utf-8")

        return Payment(
            id=model.id,
            booking_id=model.booking_id,
            amount=float(model.amount),
            currency=model.currency,
            payment_provider=model.payment_provider,
            payment_method=model.payment_method,
            status=model.status,
            provider_transaction_id=model.provider_transaction_id,
            card_last_four=model.card_last_four,
            cardholder_name=cardholder_name,
            cardholder_email=cardholder_email,
            retry_count=model.retry_count,
            payment_timestamp=model.payment_timestamp,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def _encrypt_field(self, value: Optional[str]) -> Optional[bytes]:
        if not value:
            return None
        result = await self.session.execute(
            text("SELECT pgp_sym_encrypt(:data, :key) AS encrypted"),
            {"data": value, "key": settings.AES_ENCRYPTION_KEY},
        )
        row = result.fetchone()
        return row[0] if row else None

    async def save(self, payment: Payment) -> Payment:
        cardholder_name_enc = await self._encrypt_field(payment.cardholder_name)
        cardholder_email_enc = await self._encrypt_field(payment.cardholder_email)

        model = PaymentModel(
            id=payment.id,
            booking_id=payment.booking_id,
            amount=payment.amount,
            currency=payment.currency,
            payment_provider=payment.payment_provider,
            payment_method=payment.payment_method,
            status=payment.status,
            provider_transaction_id=payment.provider_transaction_id,
            card_last_four=payment.card_last_four,
            cardholder_name=cardholder_name_enc,
            cardholder_email=cardholder_email_enc,
            retry_count=payment.retry_count,
            payment_timestamp=payment.payment_timestamp,
        )
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return await self._to_entity(model)

    async def find_by_id(self, payment_id: uuid.UUID) -> Optional[Payment]:
        result = await self.session.execute(
            select(PaymentModel).where(PaymentModel.id == payment_id)
        )
        model = result.scalar_one_or_none()
        return await self._to_entity(model) if model else None

    async def find_by_booking_id(self, booking_id: uuid.UUID) -> Optional[Payment]:
        result = await self.session.execute(
            select(PaymentModel).where(PaymentModel.booking_id == booking_id)
        )
        model = result.scalar_one_or_none()
        return await self._to_entity(model) if model else None

    async def update(self, payment: Payment) -> Payment:
        result = await self.session.execute(
            select(PaymentModel).where(PaymentModel.id == payment.id)
        )
        model = result.scalar_one_or_none()
        if not model:
            raise ValueError(f"Payment {payment.id} not found")

        model.status = payment.status
        model.provider_transaction_id = payment.provider_transaction_id
        model.retry_count = payment.retry_count
        model.payment_timestamp = payment.payment_timestamp
        model.updated_at = payment.updated_at

        if payment.cardholder_name:
            model.cardholder_name = await self._encrypt_field(payment.cardholder_name)
        if payment.cardholder_email:
            model.cardholder_email = await self._encrypt_field(payment.cardholder_email)

        await self.session.commit()
        await self.session.refresh(model)
        return await self._to_entity(model)
