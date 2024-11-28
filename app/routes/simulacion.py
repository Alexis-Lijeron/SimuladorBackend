from fastapi import APIRouter, HTTPException
from app.database import db
from app.models.simulacion import Simulacion
from pymongo.errors import PyMongoError
from bson import ObjectId
from datetime import datetime

simulacion_db = db['simulaciones']
router = APIRouter()

@router.post("/simulaciones/")
async def crear_simulacion(simulacion_data: Simulacion):
    try:
        # Insertar simulación en la base de datos
        simulacion = {
            "descripcion": simulacion_data.descripcion,
            "fecha_creacion": simulacion_data.fecha_creacion,
            "paciente_id": simulacion_data.paciente_id
        }

        resultado = simulacion_db.insert_one(simulacion)

        # Devolver la respuesta con el ID de la simulación creada
        return {"mensaje": "Simulación creada exitosamente", "id": str(resultado.inserted_id)}

    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")

@router.get("/simulaciones/", response_model=list[Simulacion])
async def obtener_simulaciones():
    try:
        simulaciones = list(simulacion_db.find())
        for simulacion in simulaciones:
            simulacion["id"] = str(simulacion["_id"])
            del simulacion["_id"]  # Eliminar _id de MongoDB para no devolverlo directamente

        return simulaciones

    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")

@router.get("/simulaciones/{simulacion_id}", response_model=Simulacion)
async def obtener_simulacion(simulacion_id: str):
    try:
        # Buscar simulación por id
        simulacion = simulacion_db.find_one({"_id": ObjectId(simulacion_id)})
        
        if not simulacion:
            raise HTTPException(status_code=404, detail="Simulación no encontrada")

        # Transformar _id en id para la respuesta
        simulacion["id"] = str(simulacion["_id"])
        del simulacion["_id"]

        return simulacion

    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")

@router.put("/simulaciones/{simulacion_id}")
async def actualizar_simulacion(simulacion_id: str, simulacion_data: Simulacion):
    try:
        # Buscar simulación por id
        simulacion = simulacion_db.find_one({"_id": ObjectId(simulacion_id)})

        if not simulacion:
            raise HTTPException(status_code=404, detail="Simulación no encontrada")

        # Actualizar los datos de la simulación
        simulacion_db.update_one(
            {"_id": ObjectId(simulacion_id)},
            {"$set": {
                "descripcion": simulacion_data.descripcion,
                "fecha_creacion": simulacion_data.fecha_creacion,
                "paciente_id": simulacion_data.paciente_id
            }}
        )

        return {"mensaje": "Simulación actualizada exitosamente"}

    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")
@router.put("/simulaciones/{simulacion_id}")
async def actualizar_simulacion(simulacion_id: str, simulacion_data: Simulacion):
    try:
        # Buscar simulación por id
        simulacion = simulacion_db.find_one({"_id": ObjectId(simulacion_id)})

        if not simulacion:
            raise HTTPException(status_code=404, detail="Simulación no encontrada")

        # Actualizar los datos de la simulación
        simulacion_db.update_one(
            {"_id": ObjectId(simulacion_id)},
            {"$set": {
                "descripcion": simulacion_data.descripcion,
                "fecha_creacion": simulacion_data.fecha_creacion,
                "paciente_id": simulacion_data.paciente_id
            }}
        )

        return {"mensaje": "Simulación actualizada exitosamente"}

    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")
