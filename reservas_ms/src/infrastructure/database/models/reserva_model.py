import uuid

from sqlalchemy import Column, DateTime, Enum, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from src.infrastructure.database.base import Base
from src.domain.entities.reserva import ReservaEstado


class ReservaModel(Base):
    __tablename__ = "reservas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    recurso_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    fecha_inicio = Column(DateTime(timezone=True), nullable=False)
    fecha_fin = Column(DateTime(timezone=True), nullable=False)
    estado = Column(
        Enum(ReservaEstado, name="reserva_estado_enum"),
        nullable=False,
        default=ReservaEstado.PENDIENTE,
    )
    notas = Column(Text, nullable=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    actualizado_en = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<ReservaModel id={self.id} estado={self.estado}>"
