from bson import ObjectId
from fastapi import APIRouter, FastAPI, HTTPException
from typing import List
from app.models.cita import Cita  # Asegúrate de que esto coincide con la ubicación de tu modelo
from app.database import db

citas_db =db['citas']
router = APIRouter()

@router.post("/citas/")
async def crear_cita(cita: Cita):
    usuario = db.user.find_one({"correo": cita.paciente_id})
    
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    # Verificar que el ID del paciente coincida con el usuario
    paciente = db.pacientes.find_one({"usuario_id": usuario["_id"]})

    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    print(f"Buscando doctor con nombre: {cita.doctor_id}")
    doctor = db.doctor.find_one({"nombre": cita.doctor_id})  # Cambia esto si necesitas buscar por otro campo
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor no encontrado: {cita.doctor_id}")

    # Si ambos existen, insertar la nueva cita
    nueva_cita = {
        "paciente_id":  paciente["_id"],
        "fecha": cita.fecha,
        "estado": cita.estado,
        "doctor_id":  doctor["_id"],
    }
    resultado = db.citas.insert_one(nueva_cita)

    return {"mensaje": "Cita creada exitosamente", "cita_id": str(resultado.inserted_id)}

@router.get("/citas/", response_model=List[Cita])
async def obtener_citas():
    try:
        citas = list(citas_db.find())
        resultados = []

        for cita in citas:
            cita['paciente_id'] = str(cita['paciente_id'])
            paciente = db.pacientes.find_one({"_id": ObjectId(cita['paciente_id'])})
            if paciente:
                # Obtener usuario usando usuario_id del paciente
                usuario = db.user.find_one({"_id": paciente['usuario_id']})
                if usuario:
                    usuario_correo = usuario.get("correo", "Correo no encontrado")
                else:
                    usuario_correo = "Usuario no encontrado"
            else:
                usuario_correo = "Paciente no encontrado"

            # Obtener doctor
            doctor = db.doctor.find_one({"_id": cita['doctor_id']})
            if doctor:
                doctor_nombre = doctor.get("nombre", "Nombre no encontrado")
            else:
                doctor_nombre = "Doctor no encontrado"

            # Crear un diccionario para el resultado
            resultado = {
                "id": str(cita['_id']),  # Convertir ObjectId a string
                "paciente_id": usuario_correo,
                "fecha": cita['fecha'],
                "estado": cita['estado'],
                "doctor_id": doctor_nombre
            }
            resultados.append(resultado)

        return resultados

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/citas/{cita_id}", response_model=Cita)
async def obtener_cita(cita_id: str):
    cita = db.citas.find_one({"_id": cita_id})
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    return cita


@router.put("/citas/{cita_id}", response_model=Cita)
async def editar_cita(cita_id: str, cita_data: Cita):
    # Verificar si la cita existe
    cita = db.citas.find_one({"_id": cita_id})
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")

    # Verificar si el paciente y el doctor existen (si se están actualizando)
    if cita_data.paciente_id:
        paciente = db.pacientes.find_one({"_id": cita_data.paciente_id})
        if not paciente:
            raise HTTPException(status_code=404, detail="Paciente no encontrado")

    if cita_data.doctor_id:
        doctor = db.doctores.find_one({"_id": cita_data.doctor_id})
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor no encontrado")

    # Actualizar la cita
    updated_cita = {k: v for k, v in cita_data.dict().items() if v is not None}
    db.citas.update_one({"_id": cita_id}, {"$set": updated_cita})

    # Devolver la cita actualizada
    return {**updated_cita, "_id": cita_id}


@router.delete("/citas/{cita_id}", response_model=Cita)
async def eliminar_cita(cita_id: str):
    cita = db.citas.find_one({"_id": cita_id})
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    db.citas.delete_one({"_id": cita_id})
    return cita
