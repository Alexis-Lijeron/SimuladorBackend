from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.database import db

roles = db['rol']
router = APIRouter()

# Modelo para el cuerpo de la solicitud
class Rol(BaseModel):
    nombre: str

# Crear un nuevo rol
@router.post("/roles/")
async def crear_rol(rol: Rol):
    try:
        if roles.find_one({"nombre": rol.nombre}):
            raise HTTPException(status_code=400, detail="Rol ya existe")
        
        nuevo_rol = {"nombre": rol.nombre}
        result = roles.insert_one(nuevo_rol)
        return {"message": "Rol creado exitosamente", "id": str(result.inserted_id)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")

# Obtener todos los roles
@router.get("/roles/")
async def obtener_roles():
    try:
        roles_list = list(roles.find())
        
        # Convertir ObjectId a string para que sea serializable
        for rol in roles_list:
            rol["id"] = str(rol["_id"])
            del rol["_id"]  # Remover _id de MongoDB si no quieres que se muestre

        return roles_list
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener los roles: {str(e)}")