from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dtos.analysis_dto import AnalyzeBookingDTO
from src.application.use_cases.analyze_booking import AnalyzeBookingUseCase
from src.domain.services.anomaly_detector_service import AnomalyDetectorService
from src.infrastructure.clients.notification_adapter import NotificationAdapter
from src.infrastructure.clients.reservas_ms_client import ReservasMsBookingHistoryClient
from src.infrastructure.config.settings import settings
from src.infrastructure.database.base import get_db
from src.infrastructure.database.repositories.sqlalchemy_anomaly_repository import (
    SQLAlchemyAnomalyEventRepository,
)
from src.infrastructure.http.dependencies import require_internal_api_key
from src.infrastructure.http.schemas.analysis_schema import (
    AnalysisResultResponse,
    AnalyzeBookingRequest,
    ErrorResponse,
)

router = APIRouter(prefix="/analysis", tags=["Analysis"])


def _build_use_case(db: AsyncSession) -> AnalyzeBookingUseCase:
    anomaly_repo = SQLAlchemyAnomalyEventRepository(db)
    history_client = ReservasMsBookingHistoryClient(
        base_url="http://reservas_ms:8000",
        api_key=settings.INTERNAL_API_KEY,
    )
    notification = NotificationAdapter(
        login_handler_url=settings.LOGIN_HANDLER_MS_URL,
        internal_api_key=settings.LOGIN_HANDLER_MS_INTERNAL_API_KEY,
        notificaciones_ms_url=settings.NOTIFICACIONES_MS_URL,
        notificaciones_api_key=settings.NOTIFICACIONES_MS_API_KEY,
    )
    detector = AnomalyDetectorService(
        booking_history_repo=history_client,
        random_anomaly_rate=settings.RANDOM_ANOMALY_RATE,
    )
    return AnalyzeBookingUseCase(detector, anomaly_repo, notification)


@router.post(
    "/booking",
    response_model=AnalysisResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze a booking for anomalies",
    description=(
        "Called by **reservas_ms** after a booking is created or updated. "
        "Runs anomaly detection (random sampling + heuristic rules).\n\n"
        "If anomalous:\n"
        "- Blocks the user via `login_handler_ms`\n"
        "- Sends alert via `notificaciones_ms` (email + Slack)\n\n"
        "Requires `X-Api-Key` header."
    ),
    responses={403: {"model": ErrorResponse, "description": "Invalid API key"}},
)
async def analyze_booking(
    body: AnalyzeBookingRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_internal_api_key),
) -> AnalysisResultResponse:
    use_case = _build_use_case(db)
    dto = AnalyzeBookingDTO(
        user_id=body.user_id,
        booking_id=body.booking_id,
        resource_id=body.resource_id,
        start_time=body.start_time,
        end_time=body.end_time,
    )
    result = await use_case.execute(dto)
    return AnalysisResultResponse(**result.model_dump())