import io
import os
import cloudinary
import cloudinary.uploader
import requests
import cv2
import mediapipe as mp
import numpy as np
from scipy.spatial import Delaunay
import trimesh
from fastapi import APIRouter, File, UploadFile, HTTPException
from typing import Dict, List
from PIL import Image
from rembg import remove

cloudinary.config(
  cloud_name='dvc8eh9sn',
  api_key='672567371692998',
  api_secret='e9EU4ZerJoWFw5sk35nJA5sHDuY',
  secure = True
)

imagenes_dir = "imagenes"
modelo_dir = "modelo_3d"

router = APIRouter()

os.makedirs(imagenes_dir, exist_ok=True)
os.makedirs(modelo_dir, exist_ok=True)

def subir_imagenes_a_cloudinary(fotos: List[UploadFile]) -> List[str]:
    urls = []
    for foto in fotos:
        resultado = cloudinary.uploader.upload(foto.file, folder="tu_carpeta")
        urls.append(resultado['url'])
    return urls

def descargar_imagen(url: str) -> np.ndarray:
    try:
        response = requests.get(url)
        if response.status_code == 200:
            image = np.array(bytearray(response.content), dtype=np.uint8)
            image = cv2.imdecode(image, cv2.IMREAD_COLOR)
            return image
        else:
            raise Exception(f"Error al descargar la imagen desde la URL: {url}")
    except Exception as e:
        print(f"Error al descargar la imagen: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al descargar la imagen: {str(e)}")

def obtener_color_promedio(imagen, puntos, alto, ancho):
    colores = []
    for punto in puntos:
        u, v = int(punto[0] * ancho), int(punto[1] * alto)
        u = np.clip(u, 0, ancho - 1)
        v = np.clip(v, 0, alto - 1)
        colores.append(imagen[v, u])
    # Promedio de los colores de los puntos en la región
    return np.mean(colores, axis=0).astype(int)
    
def asignar_colores_por_area(image_front, points_front, alto, ancho):
    # Definir zonas faciales
    ojos_izq = range(33, 134)
    ojos_der = range(362, 463)
    cejas_izq = range(70, 81)
    cejas_der = range(300, 311)
    boca = range(61, 82)
    piel = [i for i in range(len(points_front)) if not (i in ojos_izq or i in ojos_der or i in cejas_izq or i in cejas_der or i in boca)]

    # Extraer colores promedios
    color_ojos_izq = obtener_color_promedio(image_front, [points_front[i] for i in ojos_izq], alto, ancho)
    color_ojos_der = obtener_color_promedio(image_front, [points_front[i] for i in ojos_der], alto, ancho)
    color_cejas_izq = obtener_color_promedio(image_front, [points_front[i] for i in cejas_izq], alto, ancho)
    color_cejas_der = obtener_color_promedio(image_front, [points_front[i] for i in cejas_der], alto, ancho)
    color_boca = obtener_color_promedio(image_front, [points_front[i] for i in boca], alto, ancho)
    color_piel = obtener_color_promedio(image_front, [points_front[i] for i in piel], alto, ancho)

    # Inicializar colores (por defecto la piel)
    colores = np.ones_like(points_front) * color_piel
    
    # Imprimir los colores de las zonas específicas
    print("Color ojos izquierdo:", color_ojos_izq)
    print("Color ojos derecho:", color_ojos_der)
    print("Color cejas izquierdo:", color_cejas_izq)
    print("Color cejas derecho:", color_cejas_der)
    print("Color boca:", color_boca)
    print("Color piel:", color_piel)


    # Asignar colores específicos a las zonas
    for i in ojos_izq:
        colores[i] = color_ojos_izq
    for i in ojos_der:
        colores[i] = color_ojos_der
    for i in cejas_izq:
        colores[i] = color_cejas_izq
    for i in cejas_der:
        colores[i] = color_cejas_der
    for i in boca:
        colores[i] = color_boca

    return np.clip(colores, 0, 255).astype(int)
    
def generar_modelo_3d(imagenes: List[str]) -> str:
    image_left = descargar_imagen(imagenes[0])
    image_front = descargar_imagen(imagenes[1])
    image_right = descargar_imagen(imagenes[2])
    
    if image_front is None or image_left is None or image_right is None:
            raise Exception("Una o más imágenes no se pudieron cargar correctamente.")
        
    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(static_image_mode=True)

    def extract_face_landmarks(image):
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(image_rgb)
        if not results.multi_face_landmarks:
            return None
        landmarks = results.multi_face_landmarks[0].landmark
        face_points = np.array([(lm.x, lm.y, lm.z) for lm in landmarks])
        return face_points

    points_front = extract_face_landmarks(image_front)
    points_left = extract_face_landmarks(image_left)
    points_right = extract_face_landmarks(image_right)

    if points_front is None or points_left is None or points_right is None:
        raise Exception("Error al detectar los puntos en las imágenes.")

    def fusionar_puntos_con_ponderacion(points_front, points_left, points_right):
        puntos_combinados = []
        for i in range(len(points_front)):
            x = (points_front[i][0] + points_left[i][0] + points_right[i][0]) / 3
            y = (points_front[i][1] + points_left[i][1] + points_right[i][1]) / 3
            z = points_front[i][2]
            puntos_combinados.append([x, y, z])
        return np.array(puntos_combinados)

    head_3d_points = fusionar_puntos_con_ponderacion(points_front, points_left, points_right)
    # Generación de la malla 3D (triangulando los puntos)
    tri = Delaunay(head_3d_points[:, :2])
    mesh = trimesh.Trimesh(vertices=head_3d_points, faces=tri.simplices)
    
    alto, ancho, _ = image_front.shape
    colores_texturizados = asignar_colores_por_area(image_front, points_front, alto, ancho)
    colores_texturizados = np.clip(colores_texturizados * 255, 0, 255)
    assert len(colores_texturizados) == len(head_3d_points), "El número de colores no coincide con el número de vértices"
    # Crear la malla 3D texturizada
    textured_mesh = trimesh.Trimesh(vertices=head_3d_points, faces=tri.simplices, vertex_colors=colores_texturizados)

    # Exportar la malla como un archivo .obj
    glb_filename = os.path.join(modelo_dir, "cabeza_modelo_texturizado.glb")
    textured_mesh.export(glb_filename)

    return glb_filename

def subir_modelo_a_cloudinary(modelo_3d: str) -> List[str]:
    urls = []
    try:
        # Llamada asíncrona con await
        resultado = cloudinary.uploader.upload(
            modelo_3d, resource_type="raw", folder="modelos_3d"
        )
        urls.append(resultado['url'])
        return urls
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al subir el modelo 3D a Cloudinary: {str(e)}")

@router.post("/subir-fotos/")
async def subir_fotos(fotos: List[UploadFile] = File(...)) -> Dict[str, List[str]]:
    try:
        photo_urls = subir_imagenes_a_cloudinary(fotos)
        modelo_3d = generar_modelo_3d(photo_urls)
        modelo_3d_url = subir_modelo_a_cloudinary(modelo_3d)
        return {"message": ["Fotos subidas correctamente"], "url": modelo_3d_url}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al subir las fotos: {str(e)}")
    
