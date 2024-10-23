from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class Pago(BaseModel):
    id: Optional[str] = Field(None)
    monto: float
    estado: str  # Puede ser 'pendiente' o 'completado'
    fecha: datetime
