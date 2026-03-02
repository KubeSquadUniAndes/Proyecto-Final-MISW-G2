from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_validator

from src.domain.entities.reserva import ReservaEstado


class CrearReservaRequest(BaseModel):
    usuario_id: UUID
    recurso_id: UUID
    fecha_inicio: datetime
    fecha_fin: datetime
    notas: str | None = None

    @field_validator("fecha_fin")
    @classmethod
    def fecha_fin_posterior(cls, v, info):
        if "fecha_inicio" in info.data and v <= info.data["fecha_inicio"]:
            raise ValueError("fecha_fin debe ser posterior a fecha_inicio")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "usuario_id": "123e4567-e89b-12d3-a456-426614174000",
                "recurso_id": "987fcdeb-51a2-43f7-b234-426614174111",
                "fecha_inicio": "2026-04-01T10:00:00",
                "fecha_fin": "2026-04-01T12:00:00",
                "notas": "Reunión de equipo Q2",
            }
        }
    }


class ReservaResponse(BaseModel):
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


class ErrorResponse(BaseModel):
    detail: str
    codigo: str | None = None
