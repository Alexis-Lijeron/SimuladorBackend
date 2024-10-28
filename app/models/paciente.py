from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date
# Modelo Pydantic para los datos de creación del Paciente
class Paciente(BaseModel):
    usuario_id: str  # El correo del usuario
    telefono: str
    direccion: str
    fecha_nacimiento: date
    carnet_identidad: str
    sexo: Optional[str] = None  # Campo opcional, puede ser "masculino", "femenino", etc.
