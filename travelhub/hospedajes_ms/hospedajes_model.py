from enum import Enum as PyEnum
import uuid
from sqlmodel import Field, SQLModel

class TipoHospedajes(PyEnum):
    INDIVIDUAL = 'INDIVIDUAL'
    DOBLE = 'DOBLE'
    SUIT = 'SUIT'

class HospedajeBase(SQLModel):
    id: uuid.UUID = Field(default=str(uuid.uuid4()), primary_key=True)
    # age: int | None = Field(default=None, index=True)
    numero_de_personas: int = Field(default=1)
    tipo: TipoHospedajes


class Hospedaje(HospedajeBase, table=True):
    id: uuid.UUID = Field(default=str(uuid.uuid4()), primary_key=True)
    secret_name: str


class HospedajePublic(HospedajeBase):
    id: int


class HospedajeCreate(HospedajeBase):
    secret_name: str