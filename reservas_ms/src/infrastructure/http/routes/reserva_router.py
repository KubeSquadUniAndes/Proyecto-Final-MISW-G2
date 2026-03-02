from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dtos.reserva_dto import CrearReservaDTO
from src.application.use_cases.crear_reserva import CrearReservaUseCase
from src.domain.services.reserva_domain_service import ReservaDomainService
from src.infrastructure.database.base import get_db
from src.infrastructure.database.repositories.sqlalchemy_reserva_repository import (
    SQLAlchemyReservaRepository,
)
from src.infrastructure.http.schemas.reserva_schema import (
    CrearReservaRequest,
    ErrorResponse,
    ReservaResponse,
)

router = APIRouter(prefix="/reservas", tags=["Reservas"])


def _get_crear_reserva_use_case(db: AsyncSession = Depends(get_db)) -> CrearReservaUseCase:
    """Factory / wiring de dependencias (Composition Root)."""
    repo = SQLAlchemyReservaRepository(db)
    domain_service = ReservaDomainService(repo)
    return CrearReservaUseCase(repo, domain_service)


@router.post(
    "/",
    response_model=ReservaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una nueva reserva",
    responses={
        409: {"model": ErrorResponse, "description": "Conflicto de horario"},
        422: {"model": ErrorResponse, "description": "Datos inválidos"},
    },
)
async def crear_reserva(
    body: CrearReservaRequest,
    use_case: CrearReservaUseCase = Depends(_get_crear_reserva_use_case),
) -> ReservaResponse:
    """
    Crea una nueva reserva en el sistema.

    **Flujo de integración con otros microservicios:**
    - `detector_anomalias_ms` recibirá un evento al crear la reserva
      para validar si el patrón es anómalo.
    - `login_handler_ms` puede bloquear al usuario si se detectan anomalías.
    """
    try:
        dto = CrearReservaDTO(
            usuario_id=body.usuario_id,
            recurso_id=body.recurso_id,
            fecha_inicio=body.fecha_inicio,
            fecha_fin=body.fecha_fin,
            notas=body.notas,
        )
        result = await use_case.ejecutar(dto)
        return ReservaResponse(**result.model_dump())
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
