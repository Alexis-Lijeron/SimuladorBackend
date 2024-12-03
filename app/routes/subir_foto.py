import uuid
from app import cloudinary
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import requests
from typing import List
import json
import time
import cloudinary
import cloudinary.uploader
# Configuración para la API de Tripod AI
TRIPOD_API_URL = "https://api.tripo3d.ai/v2/openapi/upload"
TRIPOD_API_KEY = "tsk_u0JO9wcFhHAY800O0xhIakfbnTwxhzjJq3aESHDQTSL"  # Sustituir con tu clave API
CLOUDINARY_URL = "dvc8eh9sn"  # Cambia <your_cloud_name>
CLOUDINARY_API_KEY = "672567371692998"  # Sustituir con tu API key de Cloudinary
CLOUDINARY_API_SECRET = "e9EU4ZerJoWFw5sk35nJA5sHDuY"  # Sustituir con tu API secret de Cloudinary

router = APIRouter()


def esperar_modelo_completado(task_id: str, api_key: str, intervalo_espera: int = 10) -> str:
    """
    Espera a que el modelo esté listo consultando el estado de la tarea  cada cierto intervalo de tiempo.
    :param task_id: El ID de la tarea en Tripod AI.
    :param api_key: La clave de la API de Tripod AI.
    :param intervalo_espera: El tiempo de espera (en segundos) entre cada consulta para obtener el estado de la tarea.
    :return: URL del modelo 3D cuando la tarea se haya completado.
    """
    url = f"https://api.tripo3d.ai/v2/openapi/task/{task_id}"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    while True:
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
            raise HTTPException(status_code=response.status_code, detail=f"Error al obtener el estado de la tarea: {http_err}")
        except Exception as err:
            print(f"Other error occurred: {err}")
            raise HTTPException(status_code=500, detail=f"Error al obtener el estado de la tarea: {err}")

        if response.status_code == 200:
            task_data = response.json()
            status = task_data["data"]["status"]
            if status == "success":
                model_url = task_data["data"]["output"]["model"]
                return model_url
            elif status == "failed":
                raise HTTPException(status_code=500, detail="La tarea falló al generarse.")
            else:
                print(f"Tarea en estado {status}. Continuando esperando...")
        else:
            raise HTTPException(status_code=response.status_code, detail="Error al obtener el estado de la tarea.")
        
        time.sleep(intervalo_espera)

@router.post("/upload-photos")
async def upload_photos(files: List[UploadFile] = File(...), intervalo_espera: int = 10):
    """
    Endpoint para recibir fotos y enviarlas a la API de Tripod AI.
    :param files: Lista de fotos que el usuario sube (se esperan 3 fotos).
    :param intervalo_espera: Tiempo de espera entre cada consulta al estado de la tarea de Tripod AI (en segundos).
    :return: Respuesta de la API Tripod AI con la URL del modelo 3D.
    """
    # Validar que se reciben exactamente 3 fotos
    if len(files) != 3:
        raise HTTPException(status_code=400, detail="Se requieren exactamente 3 fotos.")

    # Validar tipos de archivo permitidos (en este caso, imágenes JPEG o PNG)
    allowed_types = {'image/jpeg', 'image/png'}
    for file in files:
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail=f"Tipo de archivo no permitido: {file.content_type}")

    try:
        # Preparar los archivos para enviar a Tripod AI
        files_to_send = {
            'file': (
                file.filename,
                await file.read(),
                file.content_type
            ) for file in files
        }

        # Cabeceras para la API de Tripod AI
        headers = {
            "Authorization": f"Bearer {TRIPOD_API_KEY}"
        }

        # Enviar la solicitud para subir las fotos
        response = requests.post(TRIPOD_API_URL, headers=headers, files=files_to_send)

        # Verificar la respuesta de Tripod AI
        if response.status_code == 200:
            data = response.json()
            file_token = data["data"]["image_token"]

            # Solicitar la generación del modelo 3D
            task_response = requests.post("https://api.tripo3d.ai/v2/openapi/task", headers=headers, json={
                "type": "image_to_model",
                "file": {
                    "type": "png",  # Ajusta según el tipo de archivo si es necesario
                    "file_token": file_token
                }
            }).json()

            # Obtener el task_id
            task_id = task_response["data"]["task_id"]

            # Esperar a que el modelo esté listo
            model_url = esperar_modelo_completado(task_id, TRIPOD_API_KEY, intervalo_espera)
            
            # Subir el modelo generado a Cloudinary
            cloudinary_url = subir_a_cloudinary(model_url)
            
            return {"message": "Modelo 3D generado y subido a Cloudinary con éxito", "model_url": cloudinary_url}
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)

    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar la solicitud: {str(e)}")
    
    # Función asincrónica para subir el archivo a Cloudinary
def subir_a_cloudinary(model_url: str) -> str:
    """
    Descargar el modelo desde la URL proporcionada y subirlo a Cloudinary.
    :param model_url: URL del modelo 3D generado por Tripod AI.
    :return: URL del modelo en Cloudinary.
    """
    try:
        # Descargar el archivo desde la URL del modelo 3D
        response = requests.get(model_url)
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Error al descargar el modelo 3D.")
        
        # Guardar el archivo temporalmente
        with open("modelo_3d.glb", "wb") as f:
            f.write(response.content)
  
        # Generar un identificador único para el archivo
        unique_id = str(uuid.uuid4())  # Genera un UUID único
        file_name = f"modelo_{unique_id}.glb"  # Nombre único para el archivo
        
        # Subir el archivo a Cloudinary (usando `upload` si es un archivo pequeño)
        upload_response = cloudinary.uploader.upload(
            "modelo_3d.glb",  # El archivo descargado
            public_id=f"taller/{file_name}",  # Ruta única en el folder "taller"
            resource_type="raw",  # Especificar que es un archivo raw
            folder="taller"  # Especificar el folder (opcional, ya implícito en public_id)
        )
        
        # Retornar la URL del modelo en Cloudinary
        return upload_response['secure_url']
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al subir el modelo a Cloudinary: {e}")