from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.reserva import Reserva


class ReservaRepositoryPort(ABC):
    """Puerto de salida: define el contrato que debe cumplir cualquier
    implementación de repositorio para Reserva."""

    @abstractmethod
    async def guardar(self, reserva: Reserva) -> Reserva:
        ...

    @abstractmethod
    async def obtener_por_id(self, reserva_id: UUID) -> Reserva | None:
        ...

    @abstractmethod
    async def listar_por_usuario(self, usuario_id: UUID) -> list[Reserva]:
        ...

    @abstractmethod
    async def actualizar(self, reserva: Reserva) -> Reserva:
        ...

    @abstractmethod
    async def eliminar(self, reserva_id: UUID) -> bool:
        ...
