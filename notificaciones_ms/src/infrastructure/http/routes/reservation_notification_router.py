from fastapi import APIRouter, Depends, HTTPException, Header, status

from src.application.dtos.reservation_confirmation_dto import ReservationConfirmationDTO
from src.application.use_cases.send_reservation_confirmation import (
    SendReservationConfirmationUseCase,
)
from src.infrastructure.config.settings import settings
from src.infrastructure.http.schemas.reservation_notification_schema import (
    ReservationConfirmationRequest,
    ReservationConfirmationResponse,
)

router = APIRouter(prefix="/notifications", tags=["Reservations"])


async def require_internal_api_key(x_api_key: str = Header(...)) -> None:
    if x_api_key != settings.INTERNAL_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing internal API key",
        )


@router.post(
    "/reservations/confirmation",
    response_model=ReservationConfirmationResponse,
    status_code=status.HTTP_200_OK,
    summary="Send reservation confirmation email",
    description=(
        "Called by **reservas_ms** when a reservation reaches 'Confirmada' status. "
        "Sends a confirmation email to the guest with full reservation details.\n\n"
        "Requires `X-Api-Key` header. Email errors are logged but do not affect "
        "the reservation status."
    ),
    responses={403: {"description": "Invalid API key"}},
)
async def send_reservation_confirmation(
    body: ReservationConfirmationRequest,
    _: None = Depends(require_internal_api_key),
) -> ReservationConfirmationResponse:
    use_case = SendReservationConfirmationUseCase()
    dto = ReservationConfirmationDTO(**body.model_dump())
    result = await use_case.execute(dto)
    return ReservationConfirmationResponse(**result.model_dump())
