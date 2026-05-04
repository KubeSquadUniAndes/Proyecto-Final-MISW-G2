from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.use_cases.confirm_payment import ConfirmPaymentUseCase
from src.application.use_cases.create_payment import CreatePaymentUseCase
from src.infrastructure.clients.notificaciones_client import NotificacionesClient
from src.infrastructure.clients.reservas_client import ReservasClient
from src.infrastructure.database.base import get_db
from src.infrastructure.database.repositories.payment_repository import PaymentRepository
from src.infrastructure.http.schemas.payment_schemas import (
    ConfirmPaymentRequest,
    CreatePaymentRequest,
    PaymentResponse,
)

router = APIRouter(tags=["payments"])


@router.post(
    "/payments",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_payment(
    request: CreatePaymentRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new payment record"""
    repository = PaymentRepository(db)
    use_case = CreatePaymentUseCase(repository)

    try:
        payment = await use_case.execute(
            booking_id=request.booking_id,
            amount=request.amount,
            currency=request.currency,
            payment_provider=request.payment_provider,
            payment_method=request.payment_method,
            card_last_four=request.card_last_four,
            cardholder_name=request.cardholder_name,
            cardholder_email=request.cardholder_email,
        )
        return PaymentResponse.model_validate(payment)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/payments/{booking_id}/confirm", response_model=PaymentResponse)
async def confirm_payment(
    booking_id: UUID,
    request: ConfirmPaymentRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Confirm payment and update booking status.

    This endpoint:
    - Updates payment status to CONFIRMED
    - Stores provider transaction ID and timestamp
    - Updates booking to 'confirmed' (with retry)
    - Sends confirmation email
    - Generates audit log
    """
    repository = PaymentRepository(db)
    reservas_client = ReservasClient()
    notificaciones_client = NotificacionesClient()
    use_case = ConfirmPaymentUseCase(repository, reservas_client, notificaciones_client)

    try:
        payment = await use_case.execute(
            booking_id=booking_id,
            provider_transaction_id=request.provider_transaction_id,
            payment_timestamp=request.payment_timestamp,
        )
        return PaymentResponse.model_validate(payment)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/payments/{booking_id}", response_model=PaymentResponse)
async def get_payment_by_booking(
    booking_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get payment by booking ID"""
    repository = PaymentRepository(db)
    payment = await repository.find_by_booking_id(booking_id)

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment for booking {booking_id} not found",
        )

    return PaymentResponse.model_validate(payment)
