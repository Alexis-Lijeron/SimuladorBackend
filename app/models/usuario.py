from pydantic import BaseModel, EmailStr
from typing import Optional

class Usuario(BaseModel):
    nombre: str
    correo: EmailStr
    password: str
    rol: Optional[str] = None  # El rol es opcional
