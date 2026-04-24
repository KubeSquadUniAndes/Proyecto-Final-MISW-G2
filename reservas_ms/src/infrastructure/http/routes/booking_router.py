from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dtos.booking_dto import (
    ApproveBookingDTO,
    CancelBookingDTO,
    CreateBookingDTO,
    RejectBookingDTO,
    UpdateBookingDTO,
)
from src.application.dtos.availability_dto import AvailabilityQueryDTO
from src.application.use_cases.approve_booking import ApproveBookingUseCase
from src.application.use_cases.cancel_booking import CancelBookingUseCase
from src.application.use_cases.check_availability import CheckAvailabilityUseCase
from src.application.use_cases.create_booking import CreateBookingUseCase
from src.application.use_cases.list_bookings import ListBookingsUseCase
from src.application.use_cases.reject_booking import RejectBookingUseCase
from src.application.use_cases.update_booking import UpdateBookingUseCase
from src.domain.services.booking_domain_service import BookingDomainService
from src.infrastructure.clients.anomaly_detector_client import AnomalyDetectorClient
from src.infrastructure.config.settings import settings
from src.infrastructure.database.base import get_db
from src.infrastructure.database.repositories.sqlalchemy_booking_repository import (
    SQLAlchemyBookingRepository,
)
from src.infrastructure.http.middleware.auth_dependency import (
    get_current_user_id,
    get_current_user_role,
)
from src.infrastructure.http.schemas.booking_schema import (
    AvailabilityResponse,
    BookingResponse,
    CreateBookingRequest,
    ErrorResponse,
    RejectBookingRequest,
    UpdateBookingRequest,
)

router = APIRouter(prefix="/bookings", tags=["Bookings"])

_anomaly_client = AnomalyDetectorClient(
    base_url=settings.DETECTOR_ANOMALIAS_MS_URL,
    api_key=settings.DETECTOR_ANOMALIAS_MS_API_KEY,
)


def _make_repo(db: AsyncSession) -> SQLAlchemyBookingRepository:
    return SQLAlchemyBookingRepository(db)


# ── GET /bookings/ ─────────────────────────────────────────────────────────────


@router.get(
    "/",
    response_model=list[BookingResponse],
    summary="List active bookings for the authenticated user",
    responses={401: {"model": ErrorResponse}},
)
async def list_bookings(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[BookingResponse]:
    repo = _make_repo(db)
    use_case = ListBookingsUseCase(repo)
    results = await use_case.execute(user_id)
    return [BookingResponse(**r.model_dump()) for r in results]


# ── GET /bookings/availability ────────────────────────────────────────────────


@router.get(
    "/availability",
    response_model=AvailabilityResponse,
    summary="Check availability for a resource in a date range",
    responses={
        400: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
    },
)
async def check_availability(
    room_id: UUID,
    start_time: datetime,
    end_time: datetime,
    room_type: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> AvailabilityResponse:
    """Get all bookings for a room in the specified date range."""
    repo = _make_repo(db)
    use_case = CheckAvailabilityUseCase(repo)
    try:
        dto = AvailabilityQueryDTO(
            room_id=room_id,
            start_time=start_time,
            end_time=end_time,
            room_type=room_type,
        )
        result = await use_case.execute(dto)
        return AvailabilityResponse(**result.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


# ── GET /bookings/{booking_id} ─────────────────────────────────────────────────


@router.get(
    "/{booking_id}",
    response_model=BookingResponse,
    summary="Get booking detail",
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
)
async def get_booking(
    booking_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> BookingResponse:
    repo = _make_repo(db)
    booking = await repo.get_by_id(booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found"
        )
    if booking.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    from src.application.use_cases.create_booking import _build_response

    return BookingResponse(**_build_response(booking).model_dump())


# ── POST /bookings/ ────────────────────────────────────────────────────────────


@router.post(
    "/",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new booking",
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
)
async def create_booking(
    body: CreateBookingRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> BookingResponse:
    repo = _make_repo(db)
    domain_service = BookingDomainService(repo)
    use_case = CreateBookingUseCase(
        repo,
        domain_service,
        anomaly_client=_anomaly_client,
    )
    try:
        dto = CreateBookingDTO(
            user_id=user_id,
            hotel_id=body.hotel_id,
            room_id=body.room_id,
            start_time=body.start_time,
            end_time=body.end_time,
            notes=body.notes,
            room_type=body.room_type,
            num_guests=body.num_guests,
            additional_guests=body.additional_guests,
            special_requests=body.special_requests,
            price_per_night=body.price_per_night,
            traveler_name=body.traveler_name,
            traveler_email=body.traveler_email,
            traveler_phone=body.traveler_phone,
            traveler_document=body.traveler_document,
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
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
)
async def update_booking(
    booking_id: UUID,
    body: UpdateBookingRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> BookingResponse:
    repo = _make_repo(db)
    domain_service = BookingDomainService(repo)
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


# ── DELETE /bookings/{booking_id} ──────────────────────────────────────────────


@router.delete(
    "/{booking_id}",
    response_model=BookingResponse,
    summary="Cancel a booking",
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
        503: {
            "model": ErrorResponse,
            "description": "Availability service unavailable",
        },
    },
)
async def cancel_booking(
    booking_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> BookingResponse:
    repo = _make_repo(db)
    use_case = CancelBookingUseCase(repo)
    try:
        dto = CancelBookingDTO(booking_id=booking_id, user_id=user_id)
        result = await use_case.execute(dto)
        return BookingResponse(**result.model_dump())
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        detail = str(exc)
        code = (
            status.HTTP_503_SERVICE_UNAVAILABLE
            if "availability" in detail.lower()
            else status.HTTP_409_CONFLICT
        )
        raise HTTPException(status_code=code, detail=detail)


# ── GET /bookings/hotel/{hotel_id} ─────────────────────────────────────────────


@router.get(
    "/hotel/{hotel_id}",
    response_model=list[BookingResponse],
    summary="List all bookings for a hotel (hotel admin only)",
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
    },
)
async def list_bookings_by_hotel(
    hotel_id: UUID,
    user_role: tuple[UUID, str] = Depends(get_current_user_role),
    db: AsyncSession = Depends(get_db),
) -> list[BookingResponse]:
    """List all bookings for a specific hotel. Only accessible by hotel admins."""
    user_id, role = user_role

    if role != "hotel":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only hotel administrators can access this endpoint",
        )

    # TODO: Validate that the hotel_id belongs to this user
    # This requires querying hospedajes_ms or having a hotel_id in the JWT
    # For now, any user with role='hotel' can query any hotel

    repo = _make_repo(db)
    from src.application.use_cases.list_bookings_by_hotel import (
        ListBookingsByHotelUseCase,
    )

    use_case = ListBookingsByHotelUseCase(repo)
    results = await use_case.execute(hotel_id)
    return [BookingResponse(**r.model_dump()) for r in results]


# ── PATCH /bookings/{booking_id}/approve ──────────────────────────────────────


@router.patch(
    "/{booking_id}/approve",
    response_model=BookingResponse,
    summary="Approve a pending booking (hotel admin)",
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
)
async def approve_booking(
    booking_id: UUID,
    user_role: tuple[UUID, str] = Depends(get_current_user_role),
    db: AsyncSession = Depends(get_db),
) -> BookingResponse:
    """Approve a pending booking and trigger payment processing."""
    user_id, role = user_role

    if role != "hotel":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only hotel administrators can approve bookings",
        )

    repo = _make_repo(db)
    use_case = ApproveBookingUseCase(repo)
    try:
        dto = ApproveBookingDTO(booking_id=booking_id, admin_user_id=user_id)
        result = await use_case.execute(dto)
        return BookingResponse(**result.model_dump())
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


# ── PATCH /bookings/{booking_id}/reject ───────────────────────────────────────


@router.patch(
    "/{booking_id}/reject",
    response_model=BookingResponse,
    summary="Reject a pending booking (hotel admin)",
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
)
async def reject_booking(
    booking_id: UUID,
    body: RejectBookingRequest,
    user_role: tuple[UUID, str] = Depends(get_current_user_role),
    db: AsyncSession = Depends(get_db),
) -> BookingResponse:
    """Reject a pending booking and release inventory."""
    user_id, role = user_role

    if role != "hotel":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only hotel administrators can reject bookings",
        )

    repo = _make_repo(db)
    use_case = RejectBookingUseCase(repo)
    try:
        dto = RejectBookingDTO(
            booking_id=booking_id,
            admin_user_id=user_id,
            rejection_reason=body.rejection_reason,
        )
        result = await use_case.execute(dto)
        return BookingResponse(**result.model_dump())
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
