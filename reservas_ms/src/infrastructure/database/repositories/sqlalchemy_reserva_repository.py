from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.reserva import Reserva, ReservaEstado
from src.domain.repositories.reserva_repository_port import ReservaRepositoryPort
from src.infrastructure.database.models.reserva_model import ReservaModel


class SQLAlchemyReservaRepository(ReservaRepositoryPort):
    """Adaptador de salida: implementación concreta del repositorio usando SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # -------------------------------------------------------------------------
    # Mappers domain <-> ORM
    # -------------------------------------------------------------------------

    def _to_domain(self, model: ReservaModel) -> Reserva:
        return Reserva(
            id=model.id,
            usuario_id=model.usuario_id,
            recurso_id=model.recurso_id,
            fecha_inicio=model.fecha_inicio,
            fecha_fin=model.fecha_fin,
            estado=ReservaEstado(model.estado),
            notas=model.notas,
            creado_en=model.creado_en,
            actualizado_en=model.actualizado_en,
        )

    def _to_model(self, reserva: Reserva) -> ReservaModel:
        return ReservaModel(
            id=reserva.id,
            usuario_id=reserva.usuario_id,
            recurso_id=reserva.recurso_id,
            fecha_inicio=reserva.fecha_inicio,
            fecha_fin=reserva.fecha_fin,
            estado=reserva.estado,
            notas=reserva.notas,
            creado_en=reserva.creado_en,
            actualizado_en=reserva.actualizado_en,
        )

    # -------------------------------------------------------------------------
    # Implementación del puerto
    # -------------------------------------------------------------------------

    async def guardar(self, reserva: Reserva) -> Reserva:
        model = self._to_model(reserva)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def obtener_por_id(self, reserva_id: UUID) -> Reserva | None:
        result = await self._session.execute(
            select(ReservaModel).where(ReservaModel.id == reserva_id)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def listar_por_usuario(self, usuario_id: UUID) -> list[Reserva]:
        result = await self._session.execute(
            select(ReservaModel).where(ReservaModel.usuario_id == usuario_id)
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    async def actualizar(self, reserva: Reserva) -> Reserva:
        result = await self._session.execute(
            select(ReservaModel).where(ReservaModel.id == reserva.id)
        )
        model = result.scalar_one_or_none()
        if not model:
            raise ValueError(f"Reserva con id={reserva.id} no encontrada")

        model.estado = reserva.estado
        model.notas = reserva.notas
        model.fecha_inicio = reserva.fecha_inicio
        model.fecha_fin = reserva.fecha_fin
        model.actualizado_en = reserva.actualizado_en

        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def eliminar(self, reserva_id: UUID) -> bool:
        result = await self._session.execute(
            select(ReservaModel).where(ReservaModel.id == reserva_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            return False
        await self._session.delete(model)
        await self._session.flush()
        return True
