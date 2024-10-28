from pydantic import BaseModel
from datetime import datetime

class Cita(BaseModel):
    paciente_id: str  # o int, dependiendo de tu implementación
    fecha: datetime
    estado: str
    doctor_id: str  # o int, dependiendo de tu implementación
