from fastapi import APIRouter, HTTPException
from app.models.doctor import Doctor, DoctorCreate
from app.database import db
from bson.objectid import ObjectId
from uuid import uuid4

doctores = db['doctor']
router = APIRouter()

@router.post("/doctores/", response_model=Doctor)
def crear_doctor(doctor: DoctorCreate):
    nuevo_doctor = doctor.dict()
    nuevo_doctor['id'] = str(uuid4())  # Generar ID único
    doctores.insert_one(nuevo_doctor)
    return nuevo_doctor

@router.get("/doctores/", response_model=list[Doctor])
async def obtener_doctores():
    doctores_list = list(doctores.find())
    for doctor in doctores_list:
        doctor['id'] = str(doctor['_id'])
        del doctor['_id']
    return doctores_list

@router.get("/doctores/{doctor_id}", response_model=Doctor)
async def obtener_doctor(doctor_id: str):
    doctor = doctores.find_one({"_id": ObjectId(doctor_id)})
    if doctor:
        doctor['id'] = str(doctor['_id'])
        del doctor['_id']
        return doctor
    raise HTTPException(status_code=404, detail="Doctor no encontrado")

@router.put("/doctores/{doctor_id}", response_model=Doctor)
async def actualizar_doctor(doctor_id: str, doctor_actualizado: Doctor):
    result = doctores.update_one(
        {"_id": ObjectId(doctor_id)},
        {"$set": doctor_actualizado.dict()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Doctor no encontrado")
    
    doctor_actualizado_db = doctores.find_one({"_id": ObjectId(doctor_id)})
    doctor_actualizado_db['id'] = str(doctor_actualizado_db['_id'])
    del doctor_actualizado_db['_id']
    
    return doctor_actualizado_db

@router.delete("/doctores/{doctor_id}")
async def eliminar_doctor(doctor_id: str):
    result = doctores.delete_one({"_id": ObjectId(doctor_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Doctor no encontrado")
    return {"mensaje": "Doctor eliminado"}
