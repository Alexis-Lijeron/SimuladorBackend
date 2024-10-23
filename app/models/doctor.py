from pydantic import BaseModel, Field
from typing import Optional

class DoctorCreate(BaseModel):
    telefono: str
    especialidad: str
    disponibilidad: str

class Doctor(BaseModel):
    id: Optional[str] = Field(None)
    telefono: str
    especialidad: str
    disponibilidad: str
