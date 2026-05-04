from fastapi import APIRouter, Depends, HTTPException, Header, status

from src.application.dtos.notification_dto import (
    BookingNotificationDTO,
    SendNotificationDTO,
)
from src.application.use_cases.send_booking_notification import SendBookingNotificationUseCase
from src.application.use_cases.send_notification import SendNotificationUseCase
from src.infrastructure.config.settings import settings
from src.infrastructure.http.schemas.notification_schema import (
    ErrorResponse,
    NotificationResultResponse,
    SendNotificationRequest,
)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


async def require_internal_api_key(x_api_key: str = Header(...)) -> None:
    if x_api_key != settings.INTERNAL_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing internal API key",
        )


@router.post(
    "/alert",
    response_model=NotificationResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Send an anomaly security alert",
    description=(
        "Called by **detector_anomalias_ms** when an anomaly is detected. "
        "Sends the alert via Email (SMTP) and Slack webhook.\n\n"
        "Requires `X-Api-Key` header."
    ),
    responses={403: {"model": ErrorResponse, "description": "Invalid API key"}},
)
async def send_alert(
    body: SendNotificationRequest,
    _: None = Depends(require_internal_api_key),
) -> NotificationResultResponse:
    use_case = SendNotificationUseCase()
    dto = SendNotificationDTO(**body.model_dump())
    result = await use_case.execute(dto)
    return NotificationResultResponse(**result.model_dump())


@router.post(
    "/booking",
    status_code=status.HTTP_200_OK,
    summary="Send a booking push notification via FCM",
    description=(
        "Called by **reservas_ms** when a booking is created or updated. "
        "Sends a push notification to the traveler's device via Firebase FCM.\n\n"
        "Requires `X-Api-Key` header."
    ),
    responses={403: {"model": ErrorResponse, "description": "Invalid API key"}},
)
async def send_booking_notification(
    body: BookingNotificationDTO,
    _: None = Depends(require_internal_api_key),
) -> dict:
    use_case = SendBookingNotificationUseCase()
    result = await use_case.execute(body)
    return result.model_dump()
