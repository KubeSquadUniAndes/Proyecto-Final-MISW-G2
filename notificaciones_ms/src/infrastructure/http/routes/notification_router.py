from fastapi import APIRouter, Depends, HTTPException, Header, status

from src.application.dtos.notification_dto import SendNotificationDTO
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
