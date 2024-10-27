from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pymongo.errors import PyMongoError
from bson import ObjectId
from datetime import date, datetime
from app.database import db
from app.models.paciente import Paciente

paciente_db=db['paciente']
router=APIRouter()

@router.post("/pacientes/")
async def crear_paciente(paciente_data: Paciente):
    try:
        # Buscar el usuario en la colección `usuarios` por correo
        usuario = db.user.find_one({"correo": paciente_data.correo})
        
        # Verificar si el usuario existe
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # Convertir `fecha_nacimiento` a un formato que MongoDB pueda almacenar
        fecha_nacimiento_datetime = datetime.combine(paciente_data.fecha_nacimiento, datetime.min.time())

        # Crear el paciente con el usuario_id del usuario encontrado
        paciente = {
            "usuario_id": usuario["_id"],  # ObjectId del usuario
            "telefono": paciente_data.telefono,
            "direccion": paciente_data.direccion,
            "fecha_nacimiento": fecha_nacimiento_datetime,  # Fecha en formato `datetime`
            "carnet_identidad": paciente_data.carnet_identidad,
            "sexo": paciente_data.sexo  # Opcional
        }

        # Insertar el nuevo paciente en la colección `pacientes`
        resultado = db.pacientes.insert_one(paciente)
        
        # Devolver la respuesta con el ID del paciente creado
        return {"mensaje": "Paciente creado exitosamente", "paciente_id": str(resultado.inserted_id)}

    except HTTPException as e:
        # Si es una excepción HTTPException, simplemente lanzarla
        raise e
    except PyMongoError as e:
        # Manejar errores de base de datos
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")
    except Exception as e:
        # Manejar cualquier otro error inesperado
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")
    
    
@router.put("/pacientes/")
async def actualizar_paciente(paciente_data: Paciente):
    try:
        # Buscar el usuario en la colección `usuarios` por correo
        usuario = db.user.find_one({"correo": paciente_data.correo})
        
        # Verificar si el usuario existe
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # Buscar el paciente usando el `usuario_id` del usuario encontrado
        paciente = db.pacientes.find_one({"usuario_id": usuario["_id"]})
        
        # Verificar si el paciente existe
        if not paciente:
            raise HTTPException(status_code=404, detail="Paciente no encontrado para este usuario")

        # Convertir `fecha_nacimiento` a un formato que MongoDB pueda almacenar
        fecha_nacimiento_datetime = datetime.combine(paciente_data.fecha_nacimiento, datetime.min.time())

        # Actualizar los campos del paciente
        actualizar_datos = {
            "telefono": paciente_data.telefono,
            "direccion": paciente_data.direccion,
            "fecha_nacimiento": fecha_nacimiento_datetime,
            "carnet_identidad": paciente_data.carnet_identidad,
            "sexo": paciente_data.sexo
        }

        # Actualizar el documento del paciente en MongoDB
        resultado = db.pacientes.update_one(
            {"usuario_id": usuario["_id"]},  # Filtro por usuario_id
            {"$set": actualizar_datos}  # Datos a actualizar
        )

        # Verificar si se realizó alguna modificación
        if resultado.modified_count == 0:
            return {"mensaje": "No se realizaron cambios en el paciente"}

        return {"mensaje": "Paciente actualizado exitosamente"}

    except HTTPException as e:
        raise e
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")