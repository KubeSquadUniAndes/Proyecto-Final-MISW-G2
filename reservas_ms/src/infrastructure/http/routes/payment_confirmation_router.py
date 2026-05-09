from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Header, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.config.settings import settings
from src.infrastructure.database.base import get_db
from src.infrastructure.database.repositories.sqlalchemy_booking_repository import (
    SQLAlchemyBookingRepository,
)

router = APIRouter(tags=["payment-confirmation"])


class PaymentConfirmRequest(BaseModel):
    status: str
    payment_id: str
    payment_status: str | None = None


def _require_internal_key(x_internal_api_key: str = Header(...)) -> None:
    if x_internal_api_key != settings.INTERNAL_API_KEY:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API key")


@router.patch("/bookings/{booking_id}/payment-confirm")
async def confirm_booking_payment(
    booking_id: UUID,
    request: PaymentConfirmRequest,
    x_internal_api_key: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    """Internal endpoint to register payment completion for a booking"""
    if x_internal_api_key != settings.INTERNAL_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API key"
        )

    repository = SQLAlchemyBookingRepository(db)
    booking = await repository.get_by_id(booking_id)

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found"
        )

    booking.payment_id = UUID(request.payment_id)
    if request.payment_status:
        booking.payment_status = request.payment_status
    await repository.update(booking)

    return {
        "status": "payment_registered",
        "booking_id": str(booking_id),
        "payment_id": request.payment_id,
    }


@router.get("/internal/bookings/{booking_id}")
async def get_booking_internal(
    booking_id: UUID,
    _: None = Depends(_require_internal_key),
    db: AsyncSession = Depends(get_db),
):
    """Internal endpoint — returns booking details for inter-service calls (e.g. pagos_ms)."""
    repository = SQLAlchemyBookingRepository(db)
    booking = await repository.get_by_id(booking_id)

    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    return {
        "booking_code": booking.booking_code or str(booking.id),
        "traveler_name": booking.traveler_name or "",
        "traveler_email": booking.traveler_email or "",
        "room_type": booking.room_type or "",
        "num_guests": booking.num_guests,
        "check_in": booking.start_time.strftime("%Y-%m-%d"),
        "check_out": booking.end_time.strftime("%Y-%m-%d"),
        "price_per_night": float(booking.price_per_night) if booking.price_per_night else 0.0,
        "total_nights": booking.total_nights or 0,
        "subtotal": float(booking.total_price) if booking.total_price else 0.0,
        "taxes": float(booking.taxes) if booking.taxes else 0.0,
        "discounts": 0.0,
        "total_amount": float(booking.final_price) if booking.final_price else 0.0,
    }
