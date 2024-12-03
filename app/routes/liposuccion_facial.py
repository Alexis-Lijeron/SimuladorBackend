import uuid
import os
from fastapi import APIRouter, HTTPException, Request
import requests
import cloudinary
import cloudinary.uploader
from pygltflib import GLTF2
import struct

# Configuración de Cloudinary
cloudinary.config(
    cloud_name="dvc8eh9sn",  # Reemplazar con tu Cloudinary Cloud Name
    api_key="672567371692998",       # Reemplazar con tu Cloudinary API Key
    api_secret="e9EU4ZerJoWFw5sk35nJA5sHDuY"  # Reemplazar con tu Cloudinary API Secret
)

router = APIRouter()

@router.post("/liposuccion_facial")
async def liposuccion_facial(request: Request):
    """
    Endpoint para procesar un modelo .glb, realizar transformaciones avanzadas,
    y subirlo a Cloudinary en la carpeta 'liposuccion_facial' con un nombre único.
    """
    try:
        # Obtener la URL del archivo del cliente
        body = await request.json()
        if "file_url" not in body:
            raise HTTPException(status_code=400, detail="Se requiere el campo 'file_url'.")
        
        file_url = body["file_url"]
        print(f"URL del archivo recibido: {file_url}")

        # Descargar el archivo desde la URL proporcionada
        print("Descargando el archivo...")
        response = requests.get(file_url)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Error al descargar el archivo desde la URL proporcionada.")
        
        input_file = "input_model.glb"
        with open(input_file, "wb") as file:
            file.write(response.content)
        print("Archivo descargado exitosamente.")

        # Cargar el modelo GLB
        print("Cargando el modelo GLB...")
        gltf = GLTF2().load(input_file)

        # Validar mallas
        if not gltf.meshes or len(gltf.meshes) == 0:
            raise HTTPException(status_code=400, detail="El archivo GLB no contiene mallas.")
        
        mesh = gltf.meshes[0]
        primitive = mesh.primitives[0]

        # Acceder al buffer de vértices
        position_accessor_index = primitive.attributes.POSITION
        accessor = gltf.accessors[position_accessor_index]
        buffer_view = gltf.bufferViews[accessor.bufferView]
        buffer = gltf.buffers[buffer_view.buffer]

        if buffer.uri is None:
            print("Modificando datos del modelo...")
            with open(input_file, "rb") as f:
                f.seek(buffer_view.byteOffset)
                buffer_data = f.read(buffer_view.byteLength)
        else:
            raise HTTPException(status_code=400, detail="Formato no soportado: URI externa encontrada.")

        # Modificar vértices con parámetros precisos
        vertex_data = buffer_data[:buffer_view.byteLength]
        new_vertex_data = bytearray(vertex_data)
        for i in range(accessor.count):
            start_index = i * 12
            x, y, z = struct.unpack_from("<fff", new_vertex_data, start_index)

            # Transformaciones específicas para liposucción facial
            x = x * 1.02 - 0.003  # Escalar y desplazar en X
            y = y * 0.99 + 0.001  # Escalar y desplazar en Y
            z = z - 2.0 + (i % 7 * 0.2)  # Desplazar en Z con un patrón basado en el índice

            # Ajustes adicionales para vértices pares
            if i % 2 == 0:
                x -= 0.002
                y *= 1.01
                z += 0.005

            # Transformaciones más agresivas en grupos de vértices específicos
            if i % 15 == 0:
                x *= 1.05
                y *= 0.95
                z -= 0.1

            struct.pack_into("<fff", new_vertex_data, start_index, x, y, z)

        # Guardar el modelo modificado
        output_file = "modified_model.glb"
        gltf.save(output_file)
        print(f"Modelo modificado guardado como {output_file}.")

        # Generar un nombre único para el archivo
        unique_id = str(uuid.uuid4())
        unique_filename = f"modelo_{unique_id}.glb"

        # Subir a Cloudinary en la carpeta 'liposuccion_facial' con un nombre único
        print("Subiendo el archivo a Cloudinary...")
        upload_response = cloudinary.uploader.upload(
            output_file,
            resource_type="raw",
            folder="liposuccion_facial",
            public_id=f"liposuccion_facial/{unique_filename}"
        )
        modified_url = upload_response["secure_url"]

        # Eliminar archivos temporales
        os.remove(input_file)
        os.remove(output_file)

        # Devolver la URL del modelo subido
        return {
            "message": "Modelo procesado y subido correctamente.",
            "modified_file_url": modified_url
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error durante el procesamiento: {e}")
