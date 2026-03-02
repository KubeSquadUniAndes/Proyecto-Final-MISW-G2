import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db_session
from app.repositories.reservation_repository import ReservationRepository
from app.schemas.reservation import (
    ReservationCreate,
    ReservationListResponse,
    ReservationResponse,
    ReservationUpdate,
)
from app.services.reservation_service import ReservationService

router = APIRouter()


def get_reservation_service(
    session: AsyncSession = Depends(get_db_session),
) -> ReservationService:
    repository = ReservationRepository(session)
    return ReservationService(repository)


@router.post("/", response_model=ReservationResponse, status_code=201)
async def create_reservation(
    data: ReservationCreate,
    service: ReservationService = Depends(get_reservation_service),
) -> ReservationResponse:
    reservation = await service.create_reservation(data)
    return ReservationResponse.model_validate(reservation, from_attributes=True)


@router.get("/{reservation_id}", response_model=ReservationResponse)
async def get_reservation(
    reservation_id: uuid.UUID,
    service: ReservationService = Depends(get_reservation_service),
) -> ReservationResponse:
    reservation = await service.get_reservation(reservation_id)
    return ReservationResponse.model_validate(reservation, from_attributes=True)


@router.get("/", response_model=ReservationListResponse)
async def list_reservations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: ReservationService = Depends(get_reservation_service),
) -> ReservationListResponse:
    items, total = await service.list_reservations(skip=skip, limit=limit)
    return ReservationListResponse(
        items=[
            ReservationResponse.model_validate(r, from_attributes=True) for r in items
        ],
        total=total,
    )


@router.put("/{reservation_id}", response_model=ReservationResponse)
async def update_reservation(
    reservation_id: uuid.UUID,
    data: ReservationUpdate,
    service: ReservationService = Depends(get_reservation_service),
) -> ReservationResponse:
    reservation = await service.update_reservation(reservation_id, data)
    return ReservationResponse.model_validate(reservation, from_attributes=True)
