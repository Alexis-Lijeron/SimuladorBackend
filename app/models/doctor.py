from pydantic import BaseModel, Field
from typing import Optional

class DoctorCreate(BaseModel):
    nombre: str
    correo: str
    telefono: str
    especialidad: str
    disponibilidad: str

class Doctor(BaseModel):
    id: Optional[str] = Field(None)
    nombre: str
    correo: str
    telefono: str
    especialidad: str
    disponibilidad: str
