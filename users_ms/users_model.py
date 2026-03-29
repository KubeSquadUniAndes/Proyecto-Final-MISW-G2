from enum import Enum as PyEnum
import uuid
from pydantic import EmailStr
from sqlmodel import Field, SQLModel


class TipoUsers(PyEnum):
    HOTEL = 'HOTEL'
    VIAJERO = 'VIAJERO'

class TipoIdentificacion(PyEnum):
    NIT = 'NIT'
    CC = 'CC'
    EXTRANJERIA = 'EXTRANJERIA'

class User(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    nombre: str = Field(nullable=False, min_length=3)
    age: int | None = Field(default=None)
    identificacion: TipoIdentificacion
    numero_identificacion: int = Field(nullable=False, min_length=6)
    email: EmailStr = Field(nullable=False)
    tipo: TipoUsers


class UserCreate(SQLModel):
    nombre: str
    age: int | None = None
    identificacion: TipoIdentificacion
    numero_identificacion: int
    email: EmailStr
    tipo: TipoUsers
