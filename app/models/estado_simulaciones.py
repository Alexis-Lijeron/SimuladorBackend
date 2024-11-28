from pydantic import BaseModel, HttpUrl
from typing import Dict, Any, Optional
from datetime import datetime
from bson import ObjectId

class EstadoSimulacion(BaseModel):
    id:Optional[str]=None
    tipo_estado: str  # 'antes' o 'despues'
    url_modelo_3d: str  # URL al modelo 3D
    fecha: datetime  # Fecha en que se guarda el estado de simulación
    simulacion_id: str