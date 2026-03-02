from src.application.dtos.reserva_dto import CrearReservaDTO, ReservaResponseDTO
from src.domain.entities.reserva import Reserva
from src.domain.repositories.reserva_repository_port import ReservaRepositoryPort
from src.domain.services.reserva_domain_service import ReservaDomainService


class CrearReservaUseCase:
    """Caso de uso: orquesta la lógica para crear una nueva reserva.

    Este use case actúa como puerto de entrada (driving port).
    Es el punto de integración con servicios externos como:
    - detector_anomalias_ms: valida si la reserva es sospechosa
    - login_handler_ms: puede bloquear al usuario si hay anomalías
    """

    def __init__(
        self,
        reserva_repo: ReservaRepositoryPort,
        domain_service: ReservaDomainService,
    ) -> None:
        self._repo = reserva_repo
        self._domain_service = domain_service

    async def ejecutar(self, dto: CrearReservaDTO) -> ReservaResponseDTO:
        # 1. Crear entidad de dominio
        reserva = Reserva(
            usuario_id=dto.usuario_id,
            recurso_id=dto.recurso_id,
            fecha_inicio=dto.fecha_inicio,
            fecha_fin=dto.fecha_fin,
            notas=dto.notas,
        )

        # 2. Validar reglas de dominio
        if not reserva.es_valida():
            raise ValueError("Las fechas de la reserva no son válidas")

        # 3. Verificar conflicto de horario
        hay_conflicto = await self._domain_service.hay_conflicto_de_horario(
            usuario_id=reserva.usuario_id,
            recurso_id=reserva.recurso_id,
            fecha_inicio=reserva.fecha_inicio,
            fecha_fin=reserva.fecha_fin,
        )
        if hay_conflicto:
            raise ValueError("Existe un conflicto de horario para este recurso")

        # 4. Persistir la reserva
        reserva_guardada = await self._repo.guardar(reserva)

        # 5. Retornar DTO de respuesta
        return ReservaResponseDTO(
            id=reserva_guardada.id,
            usuario_id=reserva_guardada.usuario_id,
            recurso_id=reserva_guardada.recurso_id,
            fecha_inicio=reserva_guardada.fecha_inicio,
            fecha_fin=reserva_guardada.fecha_fin,
            estado=reserva_guardada.estado,
            notas=reserva_guardada.notas,
            creado_en=reserva_guardada.creado_en,
            actualizado_en=reserva_guardada.actualizado_en,
        )
