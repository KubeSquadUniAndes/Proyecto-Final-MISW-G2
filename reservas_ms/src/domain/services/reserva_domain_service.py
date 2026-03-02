from datetime import datetime

from src.domain.entities.reserva import Reserva, ReservaEstado
from src.domain.repositories.reserva_repository_port import ReservaRepositoryPort


class ReservaDomainService:
    """Servicio de dominio: contiene reglas de negocio puras que no
    pertenecen a una sola entidad."""

    def __init__(self, reserva_repo: ReservaRepositoryPort) -> None:
        self._repo = reserva_repo

    async def hay_conflicto_de_horario(
        self,
        usuario_id,
        recurso_id,
        fecha_inicio: datetime,
        fecha_fin: datetime,
        excluir_reserva_id=None,
    ) -> bool:
        """Verifica si existe conflicto de horario para el mismo recurso."""
        reservas = await self._repo.listar_por_usuario(usuario_id)
        for reserva in reservas:
            if excluir_reserva_id and reserva.id == excluir_reserva_id:
                continue
            if reserva.recurso_id != recurso_id:
                continue
            if reserva.estado in (ReservaEstado.CANCELADA, ReservaEstado.COMPLETADA):
                continue
            # Solapamiento: inicio < fin_existente AND fin > inicio_existente
            if fecha_inicio < reserva.fecha_fin and fecha_fin > reserva.fecha_inicio:
                return True
        return False
