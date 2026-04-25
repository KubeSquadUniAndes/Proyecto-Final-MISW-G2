from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dtos.rate_dto import (
    CreateDiscountDTO,
    CreateRateDTO,
    UpdateDiscountDTO,
    UpdateRateDTO,
)
from src.application.use_cases.create_discount import CreateDiscountUseCase
from src.application.use_cases.create_rate import CreateRateUseCase
from src.application.use_cases.delete_discount import DeleteDiscountUseCase
from src.application.use_cases.delete_rate import DeleteRateUseCase
from src.application.use_cases.get_effective_price import GetEffectivePriceUseCase
from src.application.use_cases.get_rate import GetRateUseCase
from src.application.use_cases.list_discounts import ListDiscountsUseCase
from src.application.use_cases.list_rates import ListRatesUseCase
from src.application.use_cases.update_discount import UpdateDiscountUseCase
from src.application.use_cases.update_rate import UpdateRateUseCase
from src.domain.entities.rate import SeasonType
from src.domain.entities.room import RoomType
from src.infrastructure.database.base import get_db
from src.infrastructure.database.repositories.sqlalchemy_discount_repository import (
    SQLAlchemyDiscountRepository,
)
from src.infrastructure.database.repositories.sqlalchemy_rate_repository import (
    SQLAlchemyRateRepository,
)
from src.infrastructure.database.repositories.sqlalchemy_room_repository import (
    SQLAlchemyRoomRepository,
)
from src.infrastructure.http.dependencies import (
    TokenClaims,
    require_hotel_or_traveler_role,
    require_hotel_role,
)
from src.infrastructure.http.schemas.rate_schema import (
    CreateDiscountRequest,
    CreateRateRequest,
    DiscountResponse,
    EffectivePriceResponse,
    RateResponse,
    UpdateDiscountRequest,
    UpdateRateRequest,
)
from src.infrastructure.http.schemas.room_schema import ErrorResponse, MessageResponse

router = APIRouter(prefix="/rates", tags=["Rates"])


def _repos(db: AsyncSession):
    return SQLAlchemyRateRepository(db), SQLAlchemyDiscountRepository(db)


# ── Rates ──────────────────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=RateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear tarifa base para un tipo de habitación y temporada",
    responses={422: {"model": ErrorResponse}},
)
async def create_rate(
    body: CreateRateRequest,
    db: AsyncSession = Depends(get_db),
    claims: TokenClaims = Depends(require_hotel_role),
):
    rate_repo, _ = _repos(db)
    use_case = CreateRateUseCase(rate_repo)
    try:
        result = await use_case.execute(
            CreateRateDTO(
                hotel_id=claims.user_id,
                room_type=body.room_type,
                season=body.season,
                base_price=body.base_price,
            )
        )
        return _rate_response(result)
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.get(
    "",
    response_model=list[RateResponse],
    summary="Listar tarifas del hotel (opcionalmente filtrar por tipo de habitación)",
)
async def list_rates(
    room_type: RoomType | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    claims: TokenClaims = Depends(require_hotel_or_traveler_role),
):
    rate_repo, discount_repo = _repos(db)
    use_case = ListRatesUseCase(rate_repo, discount_repo)
    results = await use_case.execute(hotel_id=claims.user_id, room_type=room_type)
    return [_rate_response(r) for r in results]


@router.get(
    "/effective-price",
    response_model=EffectivePriceResponse,
    summary="Obtener precio efectivo (con descuento activo si aplica) para un tipo de habitación",
)
async def get_effective_price(
    hotel_id: UUID = Query(..., description="ID del hotel"),
    room_type: RoomType = Query(...),
    season: SeasonType = Query(default=SeasonType.BASE),
    db: AsyncSession = Depends(get_db),
    _: TokenClaims = Depends(require_hotel_or_traveler_role),
):
    rate_repo, discount_repo = _repos(db)
    room_repo = SQLAlchemyRoomRepository(db)
    use_case = GetEffectivePriceUseCase(rate_repo, discount_repo, room_repo)
    result = await use_case.execute(hotel_id=hotel_id, room_type=room_type, season=season)
    return EffectivePriceResponse(
        room_type=result.room_type,
        season=result.season,
        base_price=result.base_price,
        final_price=result.final_price,
        has_discount=result.has_discount,
        discount_name=result.discount_name,
    )


@router.get(
    "/{rate_id}",
    response_model=RateResponse,
    summary="Obtener una tarifa por ID",
    responses={404: {"model": ErrorResponse}},
)
async def get_rate(
    rate_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: TokenClaims = Depends(require_hotel_or_traveler_role),
):
    rate_repo, discount_repo = _repos(db)
    use_case = GetRateUseCase(rate_repo, discount_repo)
    try:
        result = await use_case.execute(rate_id)
        return _rate_response(result)
    except ValueError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.put(
    "/{rate_id}",
    response_model=RateResponse,
    summary="Actualizar precio base de una tarifa",
    responses={404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
async def update_rate(
    rate_id: UUID,
    body: UpdateRateRequest,
    db: AsyncSession = Depends(get_db),
    _: TokenClaims = Depends(require_hotel_role),
):
    rate_repo, _ = _repos(db)
    use_case = UpdateRateUseCase(rate_repo)
    try:
        result = await use_case.execute(rate_id, UpdateRateDTO(base_price=body.base_price))
        return _rate_response(result)
    except ValueError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete(
    "/{rate_id}",
    response_model=MessageResponse,
    summary="Eliminar una tarifa",
    responses={404: {"model": ErrorResponse}},
)
async def delete_rate(
    rate_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: TokenClaims = Depends(require_hotel_role),
):
    rate_repo, _ = _repos(db)
    use_case = DeleteRateUseCase(rate_repo)
    try:
        await use_case.execute(rate_id)
        return MessageResponse(message="Rate deleted successfully")
    except ValueError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc))


# ── Discounts ──────────────────────────────────────────────────────────────────

@router.post(
    "/{rate_id}/discounts",
    response_model=DiscountResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Agregar un descuento a una tarifa",
    responses={404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
async def create_discount(
    rate_id: UUID,
    body: CreateDiscountRequest,
    db: AsyncSession = Depends(get_db),
    _: TokenClaims = Depends(require_hotel_role),
):
    rate_repo, discount_repo = _repos(db)
    use_case = CreateDiscountUseCase(rate_repo, discount_repo)
    try:
        result = await use_case.execute(
            CreateDiscountDTO(
                rate_id=rate_id,
                name=body.name,
                discount_type=body.discount_type,
                value=body.value,
                start_date=body.start_date,
                end_date=body.end_date,
            )
        )
        return _discount_response(result)
    except ValueError as exc:
        status_code = (
            status.HTTP_404_NOT_FOUND
            if "not found" in str(exc)
            else status.HTTP_422_UNPROCESSABLE_ENTITY
        )
        raise HTTPException(status_code, detail=str(exc))


@router.get(
    "/{rate_id}/discounts",
    response_model=list[DiscountResponse],
    summary="Listar descuentos de una tarifa",
)
async def list_discounts(
    rate_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: TokenClaims = Depends(require_hotel_or_traveler_role),
):
    _, discount_repo = _repos(db)
    use_case = ListDiscountsUseCase(discount_repo)
    results = await use_case.execute(rate_id)
    return [_discount_response(r) for r in results]


@router.put(
    "/{rate_id}/discounts/{discount_id}",
    response_model=DiscountResponse,
    summary="Actualizar un descuento",
    responses={404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
async def update_discount(
    rate_id: UUID,
    discount_id: UUID,
    body: UpdateDiscountRequest,
    db: AsyncSession = Depends(get_db),
    _: TokenClaims = Depends(require_hotel_role),
):
    rate_repo, discount_repo = _repos(db)
    use_case = UpdateDiscountUseCase(rate_repo, discount_repo)
    try:
        result = await use_case.execute(
            discount_id,
            UpdateDiscountDTO(**body.model_dump()),
        )
        return _discount_response(result)
    except ValueError as exc:
        status_code = (
            status.HTTP_404_NOT_FOUND
            if "not found" in str(exc)
            else status.HTTP_422_UNPROCESSABLE_ENTITY
        )
        raise HTTPException(status_code, detail=str(exc))


@router.delete(
    "/{rate_id}/discounts/{discount_id}",
    response_model=MessageResponse,
    summary="Eliminar un descuento",
    responses={404: {"model": ErrorResponse}},
)
async def delete_discount(
    rate_id: UUID,
    discount_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: TokenClaims = Depends(require_hotel_role),
):
    _, discount_repo = _repos(db)
    use_case = DeleteDiscountUseCase(discount_repo)
    try:
        await use_case.execute(discount_id)
        return MessageResponse(message="Discount deleted successfully")
    except ValueError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc))


# ── Helpers ────────────────────────────────────────────────────────────────────

def _discount_response(dto) -> DiscountResponse:
    return DiscountResponse(
        id=dto.id,
        rate_id=dto.rate_id,
        name=dto.name,
        discount_type=dto.discount_type,
        value=dto.value,
        start_date=dto.start_date,
        end_date=dto.end_date,
        is_active=dto.is_active,
        created_at=dto.created_at,
        updated_at=dto.updated_at,
    )


def _rate_response(dto) -> RateResponse:
    return RateResponse(
        id=dto.id,
        hotel_id=dto.hotel_id,
        room_type=dto.room_type,
        season=dto.season,
        base_price=dto.base_price,
        final_price=dto.final_price,
        active_discount=_discount_response(dto.active_discount) if dto.active_discount else None,
        created_at=dto.created_at,
        updated_at=dto.updated_at,
    )
