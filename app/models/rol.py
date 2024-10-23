from pydantic import BaseModel
from typing import Optional

class Rol(BaseModel):
    id: Optional[str] = None
    nombre: str
