from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dtos.booking_dto import (
    ApproveBookingDTO,
    CancelBookingDTO,
    CheckInBookingDTO,
    CreateBookingDTO,
    RejectBookingDTO,
    UpdateBookingDTO,
)
from src.application.dtos.availability_dto import AvailabilityQueryDTO
from src.application.use_cases.approve_booking import ApproveBookingUseCase
from src.application.use_cases.cancel_booking import CancelBookingUseCase
from src.application.use_cases.checkin_booking import CheckInBookingUseCase
from src.application.use_cases.check_availability import CheckAvailabilityUseCase
from src.application.use_cases.resend_qr_email import ResendQrEmailUseCase
from src.application.use_cases.create_booking import CreateBookingUseCase
from src.application.use_cases.list_bookings import ListBookingsUseCase
from src.application.use_cases.reject_booking import RejectBookingUseCase
from src.application.use_cases.update_booking import UpdateBookingUseCase
from src.domain.services.booking_domain_service import BookingDomainService
from src.infrastructure.clients.anomaly_detector_client import AnomalyDetectorClient
from src.infrastructure.clients.notificaciones_client import NotificacionesClient
from src.infrastructure.clients.users_client import UsersClient
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
    BulkBookingDatesRequest,
    BulkBookingDatesResponse,
    BookingDateEntry,
    CheckInRequest,
    CreateBookingRequest,
    ErrorResponse,
    RejectBookingRequest,
    UpdateBookingRequest,
)
from src.infrastructure.messaging.sns_room_availability_publisher import (
    SNSRoomAvailabilityPublisher,
)

router = APIRouter(prefix="/bookings", tags=["Bookings"])

_anomaly_client = AnomalyDetectorClient(
    base_url=settings.DETECTOR_ANOMALIAS_MS_URL,
    api_key=settings.DETECTOR_ANOMALIAS_MS_API_KEY,
)

_notificaciones_client = NotificacionesClient(
    base_url=settings.NOTIFICACIONES_MS_URL,
    api_key=settings.NOTIFICACIONES_MS_API_KEY,
)

_users_client = UsersClient(
    base_url=settings.USERS_MS_URL,
    api_key=settings.USERS_MS_INTERNAL_API_KEY,
)

_availability_publisher = SNSRoomAvailabilityPublisher(
    topic_arn=settings.SNS_ROOM_AVAILABILITY_TOPIC_ARN,
    aws_region=settings.AWS_REGION,
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


# ── POST /bookings/bulk-dates ─────────────────────────────────────────────────


@router.post(
    "/bulk-dates",
    response_model=BulkBookingDatesResponse,
    summary="Get date ranges for multiple bookings (internal, no auth)",
)
async def get_bulk_booking_dates(
    body: BulkBookingDatesRequest,
    db: AsyncSession = Depends(get_db),
) -> BulkBookingDatesResponse:
    """Return start/end times for the given booking IDs (pending/confirmed only)."""
    repo = _make_repo(db)
    results = await repo.get_dates_by_ids(
        body.booking_ids,
        checkin=body.checkin,
        checkout=body.checkout,
    )
    return BulkBookingDatesResponse(
        bookings=[
            BookingDateEntry(
                id=r.id,
                status=r.status,
                start_time=r.start_time,
                end_time=r.end_time,
            )
            for r in results
        ]
    )


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
        availability_publisher=_availability_publisher,
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
        try:
            fcm_token = await _users_client.get_fcm_token(user_id)
            if fcm_token:
                await _notificaciones_client.send_booking_notification(
                    fcm_token=fcm_token,
                    booking_id=str(result.id),
                    booking_code=result.booking_code or "",
                    hotel_name=str(result.hotel_id),
                    check_in=result.start_time.strftime("%Y-%m-%d"),
                    check_out=result.end_time.strftime("%Y-%m-%d"),
                    status=result.status_display or result.status,
                    event_type="created",
                )
        except Exception:
            pass
        try:
            hotel_email = await _users_client.get_user_email(body.hotel_id)
            if hotel_email:
                await _notificaciones_client.notify_hotel_new_booking(
                    hotel_email=hotel_email,
                    hotel_name=str(body.hotel_id),
                    guest_name=body.traveler_name or "Viajero",
                    check_in=result.start_time.strftime("%Y-%m-%d"),
                    check_out=result.end_time.strftime("%Y-%m-%d"),
                    num_guests=body.num_guests or 1,
                    booking_code=result.booking_code or "",
                    room_type=body.room_type or "standard",
                    total_amount=float(result.final_price) if result.final_price else 0,
                )
        except Exception:
            pass
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
        repo,
        domain_service,
        anomaly_client=_anomaly_client,
        availability_publisher=_availability_publisher,
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
        try:
            fcm_token = await _users_client.get_fcm_token(user_id)
            if fcm_token:
                await _notificaciones_client.send_booking_notification(
                    fcm_token=fcm_token,
                    booking_id=str(result.id),
                    booking_code=result.booking_code or "",
                    hotel_name=str(result.hotel_id),
                    check_in=result.start_time.strftime("%Y-%m-%d"),
                    check_out=result.end_time.strftime("%Y-%m-%d"),
                    status=result.status_display or result.status,
                    event_type="modified",
                    change_summary="Fechas o datos de tu reserva fueron actualizados",
                )
        except Exception:
            pass
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
    use_case = CancelBookingUseCase(
        repo,
        availability_publisher=_availability_publisher,
        notificaciones_client=_notificaciones_client,
    )
    try:
        dto = CancelBookingDTO(booking_id=booking_id, user_id=user_id)
        result = await use_case.execute(dto)
        try:
            fcm_token = await _users_client.get_fcm_token(user_id)
            if fcm_token:
                await _notificaciones_client.send_booking_notification(
                    fcm_token=fcm_token,
                    booking_id=str(result.id),
                    booking_code=result.booking_code or "",
                    hotel_name=str(result.hotel_id),
                    check_in=result.start_time.strftime("%Y-%m-%d"),
                    check_out=result.end_time.strftime("%Y-%m-%d"),
                    status=result.status_display or result.status,
                    event_type="status_changed",
                )
        except Exception:
            pass
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
    use_case = ApproveBookingUseCase(
        repo, _notificaciones_client, availability_publisher=_availability_publisher
    )
    try:
        dto = ApproveBookingDTO(booking_id=booking_id, admin_user_id=user_id)
        result = await use_case.execute(dto)
        try:
            fcm_token = await _users_client.get_fcm_token(result.user_id)
            if fcm_token:
                await _notificaciones_client.send_booking_notification(
                    fcm_token=fcm_token,
                    booking_id=str(result.id),
                    booking_code=result.booking_code or "",
                    hotel_name=str(result.hotel_id),
                    check_in=result.start_time.strftime("%Y-%m-%d"),
                    check_out=result.end_time.strftime("%Y-%m-%d"),
                    status=result.status_display or result.status,
                    event_type="status_changed",
                )
        except Exception:
            pass
        return BookingResponse(**result.model_dump())
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


# ── POST /bookings/checkin ─────────────────────────────────────────────────────


@router.post(
    "/checkin",
    response_model=BookingResponse,
    summary="Process hotel check-in by scanning the booking QR code (hotel admin)",
    responses={
        400: {"model": ErrorResponse, "description": "Date mismatch or invalid QR"},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {
            "model": ErrorResponse,
            "description": "Already checked-in or state conflict",
        },
    },
)
async def checkin_booking(
    body: CheckInRequest,
    request: Request,
    user_role: tuple[UUID, str] = Depends(get_current_user_role),
    db: AsyncSession = Depends(get_db),
) -> BookingResponse:
    """Scan the traveler's QR code to register check-in.

    The hotel app decodes the QR (base64 PNG → QR reader → JSON payload) and
    sends the extracted booking_code and booking_id to this endpoint.
    """
    user_id, role = user_role

    if role != "hotel":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el personal del hotel puede registrar el check-in",
        )

    client_ip = request.headers.get("X-Forwarded-For") or (
        request.client.host if request.client else None
    )

    repo = _make_repo(db)
    use_case = CheckInBookingUseCase(
        repo,
        notificaciones_client=_notificaciones_client,
        users_client=_users_client,
    )
    try:
        dto = CheckInBookingDTO(
            booking_code=body.booking_code,
            booking_id=body.booking_id,
            staff_id=str(user_id),
            device=body.device,
            ip=client_ip,
        )
        result = await use_case.execute(dto)
        return BookingResponse(**result.model_dump())
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        detail = str(exc)
        # Date-related errors → 400 (not a state conflict, just wrong timing)
        if (
            "fecha" in detail.lower()
            or "expirado" in detail.lower()
            or "disponible" in detail.lower()
        ):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)


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
    use_case = RejectBookingUseCase(
        repo, availability_publisher=_availability_publisher
    )
    try:
        dto = RejectBookingDTO(
            booking_id=booking_id,
            admin_user_id=user_id,
            rejection_reason=body.rejection_reason,
        )
        result = await use_case.execute(dto)
        try:
            fcm_token = await _users_client.get_fcm_token(result.user_id)
            if fcm_token:
                await _notificaciones_client.send_booking_notification(
                    fcm_token=fcm_token,
                    booking_id=str(result.id),
                    booking_code=result.booking_code or "",
                    hotel_name=str(result.hotel_id),
                    check_in=result.start_time.strftime("%Y-%m-%d"),
                    check_out=result.end_time.strftime("%Y-%m-%d"),
                    status=result.status_display or result.status,
                    event_type="status_changed",
                )
        except Exception:
            pass
        return BookingResponse(**result.model_dump())
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


# ── POST /bookings/{booking_id}/resend-qr ─────────────────────────────────────


@router.post(
    "/{booking_id}/resend-qr",
    status_code=status.HTTP_200_OK,
    summary="Resend QR check-in email to the traveler (C5)",
    responses={
        200: {"description": "Email sent or queued"},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
)
async def resend_qr_email(
    booking_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Resend the QR check-in email to the traveler's registered address."""
    repo = _make_repo(db)
    use_case = ResendQrEmailUseCase(repo, _notificaciones_client)
    try:
        sent = await use_case.execute(booking_id=booking_id, user_id=user_id)
        return {
            "email_sent": sent,
            "message": "Email enviado correctamente."
            if sent
            else "El email no pudo enviarse, pero el QR sigue disponible en la app.",
        }
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
