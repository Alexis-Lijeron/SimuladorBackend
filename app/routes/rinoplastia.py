import uuid
from fastapi import APIRouter, HTTPException, Request
import requests
import cloudinary
import cloudinary.uploader
import os
from pygltflib import GLTF2
import struct

# Configuración de Cloudinary
cloudinary.config(
    cloud_name="dvc8eh9sn",  # Reemplazar por tu Cloudinary Cloud Name
    api_key="672567371692998",       # Reemplazar por tu Cloudinary API Key
    api_secret="e9EU4ZerJoWFw5sk35nJA5sHDuY"  # Reemplazar por tu Cloudinary API Secret
)

router = APIRouter()

@router.post("/rinoplastia")
async def rinoplastia(request: Request):
    """
    Endpoint para procesar un modelo .glb, realizar transformaciones avanzadas para rinoplastia,
    y subirlo a Cloudinary en la carpeta 'rinoplastia' con un nombre único.
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

        # Modificar vértices con transformaciones avanzadas
        vertex_data = buffer_data[:buffer_view.byteLength]
        new_vertex_data = bytearray(vertex_data)
        for i in range(accessor.count):
            start_index = i * 12
            x, y, z = struct.unpack_from("<fff", new_vertex_data, start_index)

            # Región: Punta Nasal
            if z < -8.0:
                z -= 9.0  # Reducir prominencia
                x *= 1.04  # Ensanchar fosas nasales
                y *= 1.03  # Elevar ligeramente
                if i % 3 == 0:  # Cada tercer vértice, suavizar más
                    z += 0.02
                    x *= 0.98

            # Región: Dorso Nasal
            elif -8.0 <= z <= 0.0:
                z *= 0.92  # Suavizar la joroba
                x *= 0.96  # Compactar simétricamente
                y += 0.02  # Elevar dorso nasal
                if i % 5 == 0:  # Corrección de puntos críticos
                    z += 0.05
                    y *= 1.01

            # Región: Puente Nasal (Superior)
            elif z > 0.0:
                z *= 0.88  # Reducir altura del puente
                x *= 0.94  # Compactar lateralmente
                y += 0.01  # Elevar sutilmente

            # Ajustes de simetría basados en índices
            if i % 2 == 0:  # Vértices pares
                x += 0.001
                z -= 0.001
            if i % 10 == 0:  # Vértices estratégicos
                x *= 1.02
                y *= 0.98
                z -= 0.005

            # Suavizado adicional para vértices seleccionados
            if i % 25 == 0:
                x *= 0.99
                y *= 1.02
                z += 0.01

            struct.pack_into("<fff", new_vertex_data, start_index, x, y, z)

        # Guardar el modelo modificado
        output_file = "modified_model.glb"
        gltf.save(output_file)
        print(f"Modelo modificado guardado como {output_file}.")

        # Generar un nombre único para el archivo
        unique_id = str(uuid.uuid4())
        unique_filename = f"modelo_{unique_id}.glb"

        # Subir a Cloudinary en la carpeta 'rinoplastia' con un nombre único
        print("Subiendo el archivo a Cloudinary...")
        upload_response = cloudinary.uploader.upload(
            output_file,
            resource_type="raw",
            folder="rinoplastia",
            public_id=f"rinoplastia/{unique_filename}"
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
