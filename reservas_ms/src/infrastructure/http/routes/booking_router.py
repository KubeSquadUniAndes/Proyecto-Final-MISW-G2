from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dtos.booking_dto import CreateBookingDTO, UpdateBookingDTO
from src.application.use_cases.create_booking import CreateBookingUseCase
from src.application.use_cases.update_booking import UpdateBookingUseCase
from src.domain.services.booking_domain_service import BookingDomainService
from src.infrastructure.clients.anomaly_detector_client import AnomalyDetectorClient
from src.infrastructure.config.settings import settings
from src.infrastructure.database.base import get_db
from src.infrastructure.database.repositories.sqlalchemy_booking_repository import (
    SQLAlchemyBookingRepository,
)
from src.infrastructure.http.middleware.auth_dependency import get_current_user_id
from src.infrastructure.http.schemas.booking_schema import (
    BookingResponse,
    CreateBookingRequest,
    ErrorResponse,
    UpdateBookingRequest,
)

router = APIRouter(prefix="/bookings", tags=["Bookings"])

_anomaly_client = AnomalyDetectorClient(
    base_url=settings.DETECTOR_ANOMALIAS_MS_URL,
    api_key=settings.DETECTOR_ANOMALIAS_MS_API_KEY,
)


def _make_repos(db: AsyncSession):
    repo = SQLAlchemyBookingRepository(db)
    domain_service = BookingDomainService(repo)
    return repo, domain_service


# ── POST /bookings/ ────────────────────────────────────────────────────────────


@router.post(
    "/",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new booking",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "User blocked or inactive"},
        409: {"model": ErrorResponse, "description": "Schedule conflict"},
    },
)
async def create_booking(
    body: CreateBookingRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> BookingResponse:
    """Creates a booking for the authenticated user.
    Calls detector_anomalias_ms after creation.
    Requires a valid JWT — if the user is blocked, returns 403.
    """
    repo, domain_service = _make_repos(db)
    use_case = CreateBookingUseCase(
        repo, domain_service, anomaly_client=_anomaly_client
    )
    try:
        dto = CreateBookingDTO(
            user_id=user_id,
            resource_id=body.resource_id,
            start_time=body.start_time,
            end_time=body.end_time,
            notes=body.notes,
        )
        result = await use_case.execute(dto)
        return BookingResponse(**result.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


# ── PATCH /bookings/{booking_id} ───────────────────────────────────────────────


@router.patch(
    "/{booking_id}",
    response_model=BookingResponse,
    summary="Update dates or notes of an existing booking",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "User blocked or not the owner"},
        404: {"model": ErrorResponse, "description": "Booking not found"},
        409: {"model": ErrorResponse, "description": "Schedule conflict"},
    },
)
async def update_booking(
    booking_id: UUID,
    body: UpdateBookingRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> BookingResponse:
    """Updates dates and/or notes of an existing booking.
    Only the owner can modify their own bookings.
    Calls detector_anomalias_ms after update.
    Requires a valid JWT — if the user is blocked, returns 403.
    """
    repo, domain_service = _make_repos(db)
    use_case = UpdateBookingUseCase(
        repo, domain_service, anomaly_client=_anomaly_client
    )
    try:
        dto = UpdateBookingDTO(
            booking_id=booking_id,
            user_id=user_id,
            start_time=body.start_time,
            end_time=body.end_time,
            notes=body.notes,
        )
        result = await use_case.execute(dto)
        return BookingResponse(**result.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
