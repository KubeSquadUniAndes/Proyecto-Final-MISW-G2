from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dtos.room_dto import CreateRoomDTO, UpdateRoomDTO
from src.application.use_cases.create_room import CreateRoomUseCase
from src.application.use_cases.delete_room import DeleteRoomUseCase
from src.application.use_cases.get_room import GetRoomUseCase
from src.application.use_cases.get_room_stats import GetRoomStatsUseCase
from src.application.use_cases.list_rooms import ListRoomsUseCase
from src.application.use_cases.search_rooms import SearchRoomsDTO, SearchRoomsUseCase
from src.application.use_cases.update_room import UpdateRoomUseCase
from src.infrastructure.clients.reservas_client import ReservasClient
from src.infrastructure.database.base import get_db
from src.infrastructure.database.repositories.sqlalchemy_room_repository import (
    SQLAlchemyRoomRepository,
)
from src.infrastructure.http.dependencies import (
    TokenClaims,
    require_hotel_or_traveler_role,
    require_hotel_role,
)
from src.infrastructure.http.schemas.room_schema import (
    CreateRoomRequest,
    ErrorResponse,
    MessageResponse,
    RoomResponse,
    RoomStatsResponse,
    UpdateRoomRequest,
)

router = APIRouter(prefix="/rooms", tags=["Rooms"])


def _make_repo(db: AsyncSession) -> SQLAlchemyRoomRepository:
    return SQLAlchemyRoomRepository(db)


@router.post(
    "",
    response_model=RoomResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new room",
    responses={422: {"model": ErrorResponse}},
)
async def create_room(
    body: CreateRoomRequest,
    db: AsyncSession = Depends(get_db),
    claims: TokenClaims = Depends(require_hotel_role),
):
    repo = _make_repo(db)
    use_case = CreateRoomUseCase(repo)
    try:
        result = await use_case.execute(
            CreateRoomDTO(
                hotel_id=claims.user_id,
                hotel_name=claims.full_name,
                **body.model_dump(),
            )
        )
        return RoomResponse(**result.model_dump())
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {exc}",
        )


@router.get(
    "",
    response_model=list[RoomResponse],
    summary="List all rooms",
)
async def list_rooms(
    hotel_id: UUID | None = Query(
        default=None, description="Filtrar habitaciones por hotel"
    ),
    db: AsyncSession = Depends(get_db),
    _: TokenClaims = Depends(require_hotel_or_traveler_role),
):
    repo = _make_repo(db)
    use_case = ListRoomsUseCase(repo)
    results = await use_case.execute(hotel_id=hotel_id)
    return [RoomResponse(**r.model_dump()) for r in results]


@router.get(
    "/search",
    response_model=list[RoomResponse],
    summary="Buscar habitaciones disponibles por destino, huéspedes y fechas",
    responses={422: {"model": ErrorResponse}},
)
async def search_rooms(
    checkin: datetime = Query(..., description="Fecha de check-in (ISO 8601)"),
    checkout: datetime = Query(..., description="Fecha de check-out (ISO 8601)"),
    destination: str | None = Query(default=None, description="Ciudad o destino"),
    guests: int | None = Query(default=None, ge=1, description="Número de huéspedes"),
    db: AsyncSession = Depends(get_db),
    _: TokenClaims = Depends(require_hotel_or_traveler_role),
):
    repo = _make_repo(db)
    use_case = SearchRoomsUseCase(repo, ReservasClient())
    try:
        results = await use_case.execute(
            SearchRoomsDTO(
                destination=destination,
                guests=guests,
                checkin=checkin,
                checkout=checkout,
            )
        )
        return [RoomResponse(**r.model_dump()) for r in results]
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.get(
    "/stats",
    response_model=RoomStatsResponse,
    summary="Get room statistics",
)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    _: TokenClaims = Depends(require_hotel_role),
):
    repo = _make_repo(db)
    use_case = GetRoomStatsUseCase(repo)
    result = await use_case.execute()
    return RoomStatsResponse(**result.model_dump())


@router.get(
    "/{room_id}",
    response_model=RoomResponse,
    summary="Get a room by ID",
    responses={404: {"model": ErrorResponse}},
)
async def get_room(
    room_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: TokenClaims = Depends(require_hotel_or_traveler_role),
):
    repo = _make_repo(db)
    use_case = GetRoomUseCase(repo)
    try:
        result = await use_case.execute(room_id)
        return RoomResponse(**result.model_dump())
    except ValueError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.put(
    "/{room_id}",
    response_model=RoomResponse,
    summary="Update a room",
    responses={404: {"model": ErrorResponse}},
)
async def update_room(
    room_id: UUID,
    body: UpdateRoomRequest,
    db: AsyncSession = Depends(get_db),
    _: TokenClaims = Depends(require_hotel_role),
):
    repo = _make_repo(db)
    use_case = UpdateRoomUseCase(repo)
    try:
        result = await use_case.execute(room_id, UpdateRoomDTO(**body.model_dump()))
        return RoomResponse(**result.model_dump())
    except ValueError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete(
    "/{room_id}",
    response_model=MessageResponse,
    summary="Delete a room",
    responses={404: {"model": ErrorResponse}},
)
async def delete_room(
    room_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: TokenClaims = Depends(require_hotel_role),
):
    repo = _make_repo(db)
    use_case = DeleteRoomUseCase(repo)
    try:
        await use_case.execute(room_id)
        return MessageResponse(message="Room deleted successfully")
    except ValueError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc))
