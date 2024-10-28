from fastapi import APIRouter, HTTPException
from app.models.pago import Pago
from app.database import db
from bson.objectid import ObjectId
from datetime import datetime

pagos_db = db['pago']
usuarios = db['usuario']
router = APIRouter()

@router.post("/pagos/", response_model=Pago)
def crear_pago(pago: Pago):
    usuario = usuarios.find_one({"_id": ObjectId(pago.usuario_id)})
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    nuevo_pago = pago.dict()
    if isinstance(nuevo_pago['fecha'], datetime):  # Si es un objeto datetime, asegúrate de manejarlo correctamente
        nuevo_pago['fecha'] = nuevo_pago['fecha']
    pagos_db.insert_one(nuevo_pago)
    nuevo_pago['id'] = str(nuevo_pago['_id'])
    del nuevo_pago['_id']
    return nuevo_pago

@router.get("/pagos/", response_model=list[Pago])
async def obtener_pagos():
    pagos = list(pagos_db.find())
    for pago in pagos:
        pago['id'] = str(pago['_id'])
        del pago['_id']
    return pagos

@router.get("/pagos/{pago_id}", response_model=Pago)
async def obtener_pago_por_id(pago_id: str):
    pago = pagos_db.find_one({"_id": ObjectId(pago_id)})
    if pago:
        pago['id'] = str(pago['_id'])
        return pago
    raise HTTPException(status_code=404, detail="Pago no encontrado")

@router.put("/pagos/{pago_id}", response_model=Pago)
async def actualizar_pago(pago_id: str, pago_actualizado: Pago):
    result = pagos_db.update_one(
        {"_id": ObjectId(pago_id)},
        {"$set": pago_actualizado.dict()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    
    pago_actualizado_db = pagos_db.find_one({"_id": ObjectId(pago_id)})
    pago_actualizado_db['id'] = str(pago_actualizado_db['_id'])
    del pago_actualizado_db['_id']
    
    return pago_actualizado_db

@router.delete("/pagos/{pago_id}")
async def eliminar_pago(pago_id: str):
    result = pagos_db.delete_one({"_id": ObjectId(pago_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    return {"mensaje": "Pago eliminado"}
