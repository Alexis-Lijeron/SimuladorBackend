from bson import ObjectId
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Simulacion(BaseModel):
    id:Optional[str]=None
    descripcion: str  # Descripción de la simulación
    fecha_creacion: datetime  # Fecha de creación de la simulación
    paciente_id: str