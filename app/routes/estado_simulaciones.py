from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pymongo.errors import PyMongoError
from bson import ObjectId
from datetime import datetime
from app.database import db
from app.models.estado_simulaciones import EstadoSimulacion
from app.routes.subir_foto import subir_a_cloudinary

estado_simulaciones_db = db['estado_simulaciones']
router = APIRouter()

# Función para convertir ObjectId a string
def str_to_objectid(id_str: str) -> ObjectId:
    return ObjectId(id_str)

@router.get("/estado_simulaciones/por_simulacion/{simulacion_id}", response_model=List[EstadoSimulacion])
async def obtener_estados_por_simulacion(simulacion_id: str):
    """
    Obtiene todos los estados de simulación asociados a un simulacion_id.
    """
    try:
        # Buscar todos los estados asociados al simulacion_id
        estados = list(estado_simulaciones_db.find({"simulacion_id": simulacion_id}))

        # Convertir ObjectId a string y formatear los datos
        for estado in estados:
            estado["id"] = str(estado["_id"])
            del estado["_id"]

        if not estados:
            raise HTTPException(status_code=404, detail="No se encontraron estados para este simulacion_id")

        return estados

    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")
    
#Funcion para obtener todos los estados de simulaciones
@router.get("/estado_simulaciones/", response_model=List[EstadoSimulacion])
async def obtener_estado_simulaciones():
    try:
        # Obtener todos los estados de simulaciones desde la base de datos
        estados = list(estado_simulaciones_db.find())
        
        for estado in estados:
            estado["id"] = str(estado["_id"])
            del estado["_id"]
        return estados

    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")

#Funcion para crear un estado de simulacion
@router.post("/estado_simulaciones/", response_model=EstadoSimulacion)
async def crear_estado_simulacion(estado_data: EstadoSimulacion):
    try:
        # Convertir la fecha de creación a UTC
        fecha_creacion = datetime.utcnow()

        # Crear el documento del estado de simulación
        estado = {
            "tipo_estado": estado_data.tipo_estado,
            "url_modelo_3d": estado_data.url_modelo_3d,  # URL proporcionada directamente desde el frontend
            "fecha": fecha_creacion,
            "simulacion_id": estado_data.simulacion_id
        }

        # Insertar el estado en la base de datos
        resultado = estado_simulaciones_db.insert_one(estado)

        # Convertir el ID generado a string y devolver en la respuesta
        estado_data.id = str(resultado.inserted_id)
        return estado_data

    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")

#Funcion para obtener un estado de simulacion por id
@router.get("/estado_simulaciones/{estado_id}", response_model=EstadoSimulacion)
async def obtener_estado_simulacion(estado_id: str):
    try:
        # Buscar el estado de simulación por ID
        estado = estado_simulaciones_db.find_one({"_id": str_to_objectid(estado_id)})

        if not estado:
            raise HTTPException(status_code=404, detail="Estado de simulación no encontrado")

        # Convertir _id a id
        estado["id"] = str(estado["_id"])
        del estado["_id"]

        return EstadoSimulacion(**estado)

    except HTTPException as e:
        raise e
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")

from fastapi.responses import JSONResponse

#Actualizar un estado de simulacion por id
@router.put("/estado_simulaciones/{estado_id}", response_model=dict)
async def actualizar_estado_simulacion(estado_id: str, estado_data: EstadoSimulacion):
    try:
        # Buscar el estado de simulación por ID
        estado = estado_simulaciones_db.find_one({"_id": str_to_objectid(estado_id)})

        if not estado:
            raise HTTPException(status_code=404, detail="Estado de simulación no encontrado")

        # Convertir los datos a un formato adecuado para la actualización
        actualizar_datos = estado_data.dict(exclude_unset=True)

        # Actualizar el estado en la base de datos
        resultado = estado_simulaciones_db.update_one(
            {"_id": str_to_objectid(estado_id)},
            {"$set": actualizar_datos}
        )

        if resultado.modified_count == 0:
            raise HTTPException(status_code=404, detail="No se realizaron cambios en el estado de simulación")

        return JSONResponse(content={"mensaje": "Estado de simulación actualizado exitosamente"})

    except HTTPException as e:
        raise e
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")

#Eliminar un estado de simulacion por id
@router.delete("/estado_simulaciones/{estado_id}", response_model=dict)
async def eliminar_estado_simulacion(estado_id: str):
    try:
        # Eliminar el estado de simulación por ID
        resultado = estado_simulaciones_db.delete_one({"_id": str_to_objectid(estado_id)})

        if resultado.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Estado de simulación no encontrado")

        return {"mensaje": "Estado de simulación eliminado exitosamente"}

    except HTTPException as e:
        raise e
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")

#Elimina todos los estados de simulación asociados al simulacion_id.
@router.delete("/estado_simulaciones/por_simulacion/{simulacion_id}", response_model=dict)
async def eliminar_estados_por_simulacion(simulacion_id: str):
    try:
        # Convertir el ID de simulación a ObjectId
        simulacion_object_id = str_to_objectid(simulacion_id)

        # Buscar y eliminar los estados asociados al simulacion_id
        resultado = estado_simulaciones_db.delete_many({"simulacion_id": simulacion_id})

        # Verificar si se eliminó al menos un documento
        if resultado.deleted_count == 0:
            raise HTTPException(status_code=404, detail="No se encontraron estados de simulación para este simulacion_id")

        return {"mensaje": f"Se eliminaron {resultado.deleted_count} estado(s) de simulación asociado(s) a la simulación con ID: {simulacion_id}"}

    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")
