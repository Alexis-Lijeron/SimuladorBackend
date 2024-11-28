from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pymongo.errors import PyMongoError
from bson import ObjectId
from datetime import datetime
from app.database import db
from app.models.estado_simulaciones import EstadoSimulacion
from app.routes.subir_foto1 import subir_a_cloudinary

estado_simulaciones_db = db['estado_simulaciones']
router = APIRouter()

# Función para convertir ObjectId a string
def str_to_objectid(id_str: str) -> ObjectId:
    return ObjectId(id_str)

@router.get("/estado_simulaciones/", response_model=List[EstadoSimulacion])
async def obtener_estado_simulaciones():
    try:
        # Obtener todos los estados de simulaciones desde la base de datos
        estados = list(estado_simulaciones_db.find())
        
        for estado in estados:
            estado["id"] = str(estado["_id"])
            del estado["_id"]
            
            # Si hay alguna propiedad adicional, puedes formatearla aquí (ejemplo)
            # if "usuario_id" in estado:
            #     usuario = db.user.find_one({"_id": estado["usuario_id"]})
            #     if usuario and "correo" in usuario:
            #         estado["usuario_id"] = usuario["correo"]
            #     else:
            #         estado["usuario_id"] = None
        
        return estados

    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")

@router.post("/estado_simulaciones/", response_model=EstadoSimulacion)
async def crear_estado_simulacion(estado_data: EstadoSimulacion):
    try:
        # Subir el modelo 3D a Cloudinary y obtener la URL
        url_modelo_3d = subir_a_cloudinary(estado_data.url_modelo_3d)

        # Convertir la fecha de creación
        fecha_creacion = datetime.utcnow()

        # Crear un nuevo estado de simulación en la base de datos
        estado = {
            "url_modelo_3d": url_modelo_3d,
            "fecha": fecha_creacion,
            **estado_data.dict(exclude_unset=True)  # Incluye los campos del modelo que no son None
        }

        # Insertar el estado en la base de datos
        resultado = estado_simulaciones_db.insert_one(estado)

        # Devolver el objeto con el ID generado
        estado_data.id = str(resultado.inserted_id)
        return estado_data

    except HTTPException as e:
        raise e
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")

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

@router.put("/estado_simulaciones/{estado_id}", response_model=EstadoSimulacion)
async def actualizar_estado_simulacion(estado_id: str, estado_data: EstadoSimulacion):
    try:
        # Buscar el estado de simulación por ID
        estado = estado_simulaciones_db.find_one({"_id": str_to_objectid(estado_id)})

        if not estado:
            raise HTTPException(status_code=404, detail="Estado de simulación no encontrado")

        # Subir el modelo 3D si se proporciona uno nuevo
        if estado_data.url_modelo_3d:
            url_modelo_3d = await subir_a_cloudinary(estado_data.url_modelo_3d)
            estado_data.url_modelo_3d = url_modelo_3d

        # Convertir los datos a un formato adecuado para la actualización
        actualizar_datos = estado_data.dict(exclude_unset=True)

        # Actualizar el estado en la base de datos
        resultado = estado_simulaciones_db.update_one(
            {"_id": str_to_objectid(estado_id)},
            {"$set": actualizar_datos}
        )

        if resultado.modified_count == 0:
            raise HTTPException(status_code=404, detail="No se realizaron cambios en el estado de simulación")

        return { "mensaje": "Estado de simulación actualizado exitosamente" }

    except HTTPException as e:
        raise e
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")

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
