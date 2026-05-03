from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Header, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.booking import BookingStatus
from src.infrastructure.database.base import get_db
from src.infrastructure.database.repositories.sqlalchemy_booking_repository import SQLAlchemyBookingRepository
from src.infrastructure.config.settings import settings

router = APIRouter(tags=["payment-confirmation"])


class PaymentConfirmRequest(BaseModel):
    status: str
    payment_id: str


@router.patch("/bookings/{booking_id}/payment-confirm")
async def confirm_booking_payment(
    booking_id: UUID,
    request: PaymentConfirmRequest,
    x_internal_api_key: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    """Internal endpoint to register payment completion for a booking"""
    if x_internal_api_key != settings.INTERNAL_API_KEY:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API key")
    
    repository = SQLAlchemyBookingRepository(db)
    booking = await repository.get_by_id(booking_id)
    
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    
    # Registrar el payment_id en la reserva
    booking.payment_id = UUID(request.payment_id)
    updated_booking = await repository.update(booking)
    print(f"DEBUG: Updated booking payment_id: {updated_booking.payment_id}")
    
    return {"status": "payment_registered", "booking_id": str(booking_id), "payment_id": request.payment_id}
