from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pymongo.errors import PyMongoError
from bson import ObjectId
from datetime import date, datetime
from app.database import db
from app.models.paciente import Paciente

paciente_db=db['pacientes']
router=APIRouter()

@router.get("/pacientes/",response_model=list[Paciente])
async def obtener_pacientes():
    try:
        pacientes = list(paciente_db.find()) 
        for paciente in pacientes:
            paciente["id"] = str(paciente["_id"])
            del paciente["_id"] 
            if "usuario_id" in paciente:
                usuario = db.user.find_one({"_id": paciente["usuario_id"]})
                
                # Reemplazar usuario_id con el correo del usuario si existe
                if usuario and "correo" in usuario:
                    paciente["usuario_id"] = usuario["correo"]
                else:
                    paciente["usuario_id"] = None  # O algún valor predeterminado en caso de que no se encuentre el usuario

        return pacientes

    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")

@router.post("/pacientes/")
async def crear_paciente(paciente_data: Paciente):
    try:
        # Buscar el usuario en la colección `usuarios` por correo
        usuario = db.user.find_one({"correo": paciente_data.usuario_id})
        
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
        usuario = db.user.find_one({"correo": paciente_data.usuario_id})
        
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
    
@router.delete("/pacientes/{correo}")
async def eliminar_paciente(correo: str):
    try:
        # Buscar el usuario en la colección `usuarios` por correo
        usuario = db.user.find_one({"correo": correo})
        
        # Verificar si el usuario existe
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Buscar el paciente usando el `usuario_id` del usuario encontrado
        paciente = db.pacientes.find_one({"usuario_id": usuario["_id"]})
        
        # Verificar si el paciente existe
        if not paciente:
            raise HTTPException(status_code=404, detail="Paciente no encontrado para este usuario")
        
        # Eliminar el paciente de la colección `pacientes`
        resultado = db.pacientes.delete_one({"usuario_id": usuario["_id"]})
        
        # Verificar si se eliminó un documento
        if resultado.deleted_count == 0:
            raise HTTPException(status_code=500, detail="No se pudo eliminar el paciente")
        
        return {"mensaje": "Paciente eliminado exitosamente"}

    except HTTPException as e:
        raise e
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")

@router.get("/pacientes/{correo}")
async def obtener_paciente(correo: str):
    try:
        # Buscar el usuario en la colección `usuarios` por correo
        usuario = db.user.find_one({"correo": correo})
        
        # Verificar si el usuario existe
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Buscar el paciente usando el `usuario_id` del usuario encontrado
        paciente = db.pacientes.find_one({"usuario_id": usuario["_id"]})
        
        # Verificar si el paciente existe
        if not paciente:
            raise HTTPException(status_code=404, detail="Paciente no encontrado para este usuario")
        
        # Formatear la respuesta con los datos del paciente
        paciente_data = {
            "usuario_id": str(paciente["usuario_id"]),
            "telefono": paciente["telefono"],
            "direccion": paciente["direccion"],
            "fecha_nacimiento": paciente["fecha_nacimiento"].isoformat(),
            "carnet_identidad": paciente["carnet_identidad"],
            "sexo": paciente.get("sexo")
        }

        return {"mensaje": "Paciente encontrado", "paciente": paciente_data}

    except HTTPException as e:
        raise e
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")

@router.get("/pacientes/")
async def obtener_todos_los_pacientes():
    try:
        # Obtener todos los documentos de la colección `pacientes`
        pacientes = db.pacientes.find()

        # Crear una lista para almacenar los datos de cada paciente
        lista_pacientes = []
        
        # Recorrer cada paciente y obtener el correo del usuario asociado
        for paciente in pacientes:
            # Buscar el usuario asociado al paciente usando `usuario_id`
            usuario = db.user.find_one({"_id": paciente["usuario_id"]})
            
            # Si el usuario existe, incluir el correo en los datos del paciente
            if usuario:
                paciente_data = {
                    "correo": usuario["correo"],
                    "telefono": paciente["telefono"],
                    "direccion": paciente["direccion"],
                    "fecha_nacimiento": paciente["fecha_nacimiento"].isoformat(),
                    "carnet_identidad": paciente["carnet_identidad"],
                    "sexo": paciente.get("sexo")
                }
                lista_pacientes.append(paciente_data)

        return {"mensaje": "Pacientes encontrados", "pacientes": lista_pacientes}

    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")


    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")

@router.delete("/pacientes/eliminarId/{id}")
async def eliminar_paciente(id: str):
    try:
        # Verificar que el id tiene 24 caracteres
        if len(id) != 24:
            raise HTTPException(status_code=400, detail="ID proporcionado no es válido. Debe tener 24 caracteres hexadecimales.")
        usuario_id = ObjectId(id)
        usuario = db.user.find_one({"_id": usuario_id})
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        resultado_paciente = db.pacientes.delete_one({"usuario_id": usuario_id})
        if resultado_paciente.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Paciente no encontrado para este usuario")
        
        return {"mensaje": "Paciente eliminado exitosamente"}

    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")

