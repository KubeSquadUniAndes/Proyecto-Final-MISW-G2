from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class ReservaEstado(str, Enum):
    PENDIENTE = "pendiente"
    CONFIRMADA = "confirmada"
    CANCELADA = "cancelada"
    COMPLETADA = "completada"


@dataclass
class Reserva:
    usuario_id: UUID
    recurso_id: UUID
    fecha_inicio: datetime
    fecha_fin: datetime
    id: UUID = field(default_factory=uuid4)
    estado: ReservaEstado = ReservaEstado.PENDIENTE
    notas: str | None = None
    creado_en: datetime = field(default_factory=datetime.utcnow)
    actualizado_en: datetime = field(default_factory=datetime.utcnow)

    def confirmar(self) -> None:
        if self.estado != ReservaEstado.PENDIENTE:
            raise ValueError(f"No se puede confirmar una reserva en estado '{self.estado}'")
        self.estado = ReservaEstado.CONFIRMADA
        self.actualizado_en = datetime.utcnow()

    def cancelar(self) -> None:
        if self.estado in (ReservaEstado.CANCELADA, ReservaEstado.COMPLETADA):
            raise ValueError(f"No se puede cancelar una reserva en estado '{self.estado}'")
        self.estado = ReservaEstado.CANCELADA
        self.actualizado_en = datetime.utcnow()

    def completar(self) -> None:
        if self.estado != ReservaEstado.CONFIRMADA:
            raise ValueError(f"No se puede completar una reserva en estado '{self.estado}'")
        self.estado = ReservaEstado.COMPLETADA
        self.actualizado_en = datetime.utcnow()

    def es_valida(self) -> bool:
        return self.fecha_inicio < self.fecha_fin
