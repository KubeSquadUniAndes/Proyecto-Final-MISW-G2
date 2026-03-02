from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_validator

from src.domain.entities.reserva import ReservaEstado


class CrearReservaDTO(BaseModel):
    usuario_id: UUID
    recurso_id: UUID
    fecha_inicio: datetime
    fecha_fin: datetime
    notas: str | None = None

    @field_validator("fecha_fin")
    @classmethod
    def fecha_fin_debe_ser_posterior(cls, v, info):
        if "fecha_inicio" in info.data and v <= info.data["fecha_inicio"]:
            raise ValueError("fecha_fin debe ser posterior a fecha_inicio")
        return v


class ReservaResponseDTO(BaseModel):
    id: UUID
    usuario_id: UUID
    recurso_id: UUID
    fecha_inicio: datetime
    fecha_fin: datetime
    estado: ReservaEstado
    notas: str | None
    creado_en: datetime
    actualizado_en: datetime

    model_config = {"from_attributes": True}
