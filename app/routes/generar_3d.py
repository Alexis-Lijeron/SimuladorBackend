import subprocess
import os
import uuid
import cv2
import numpy as np
from fastapi import APIRouter, File, HTTPException, UploadFile
import bpy
import sys
import shutil

router = APIRouter()

images_path = "imagenes"
output_path = "modelo_3d"

os.makedirs(images_path, exist_ok=True)
os.makedirs(output_path, exist_ok=True)

@router.post("/generate_model/")
async def generate_model(files: list[UploadFile] = File(...)):
    # Crear un ID único para el conjunto de imágenes
    model_id = str(uuid.uuid4())
    model_images_path = os.path.join(images_path, model_id)
    os.makedirs(model_images_path, exist_ok=True)

    # Guardar imágenes subidas
    for file in files:
        image_path = os.path.join(model_images_path, file.filename)
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    
    # Generar la ruta de salida para el modelo 3D
    model_output_path = os.path.join(output_path, f"{model_id}.obj")

    # Intentar crear el modelo 3D llamando al script de Blender
    try:
        run_blender_script(model_images_path, model_output_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en Blender: {str(e)}")

    return {"model_id": model_id, "model_path": model_output_path}

def run_blender_script(images_dir, output_path):
    # Ejecutar Blender en modo background y correr el script de generación de modelo 3D
    command = [
        "blender", "--background", "--python", "generate_model.py", "--", images_dir, output_path
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    
    # Verificar si el comando se ejecutó correctamente
    if result.returncode != 0:
        raise Exception(result.stderr)