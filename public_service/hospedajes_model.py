from enum import Enum as PyEnum
import uuid
from sqlmodel import Field, SQLModel

class TipoHospedajes(PyEnum):
    INDIVIDUAL = 'INDIVIDUAL'
    DOBLE = 'DOBLE'
    SUIT = 'SUIT'


class Hospedaje(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    numero_de_personas: int = Field(default=1)
    tipo: TipoHospedajes
    secret_name: str


class HospedajeCreate(SQLModel):
    numero_de_personas: int = 1
    tipo: TipoHospedajes
    secret_name: str
