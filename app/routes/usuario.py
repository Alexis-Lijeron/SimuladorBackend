from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.utils import hash_contraseña, verificar_contraseña
from app.utils import crear_token_acceso, verificar_token, verificar_admin
from pymongo.errors import PyMongoError
from app.database import db
from jose import JWTError
from pydantic import BaseModel

usuarios = db['user']
roles = db['rol']  # Nueva colección de roles
router = APIRouter()

# Dependencia para obtener el token de OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Dependencia para verificar el token
def obtener_usuario_actual(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = verificar_token(token)
    if payload is None:
        raise credentials_exception
    return payload

# Crear un usuario con rol por defecto
@router.post("/usuarios/")
async def crear_usuario(usuario: Usuario):
    # Verificar si el rol 'admin' fue solicitado
    if usuario.rol == "admin":
        raise HTTPException(status_code=403, detail="No puedes asignarte el rol 'admin'")

    # Buscar el rol 'paciente'
    rol_paciente = roles.find_one({"nombre": "paciente"})
    if not rol_paciente:
        # Si el rol paciente no existe, crearlo
        rol_paciente = {"nombre": "paciente"}
        roles.insert_one(rol_paciente)
    
    # Si el usuario no especifica un rol, asignar 'paciente'
    rol_asignado = roles.find_one({"nombre": usuario.rol}) if usuario.rol else rol_paciente

    if usuarios.find_one({"correo": usuario.correo}):
        raise HTTPException(status_code=400, detail="Correo ya registrado")

    usuario_con_hashed_password = usuario.dict()
    usuario_con_hashed_password["password"] = hash_contraseña(usuario.password)
    usuario_con_hashed_password["rol"] = rol_asignado["nombre"]  # Asignar el rol al usuario

    usuarios.insert_one(usuario_con_hashed_password)
    
    return {"message": "Usuario creado exitosamente", "rol_asignado": rol_asignado["nombre"]}

# Modelo para los datos de login
class LoginData(BaseModel):
    correo: str
    password: str

# Login para obtener un token JWT y devolver el rol
@router.post("/login/")
async def login(datos: LoginData):
    try:
        # Buscar usuario por correo
        usuario = usuarios.find_one({"correo": datos.correo})
        if not usuario:
            raise HTTPException(status_code=400, detail="Correo o contraseña incorrectos")

        # Verificar la contraseña
        if not verificar_contraseña(datos.password, usuario["password"]):
            raise HTTPException(status_code=400, detail="Correo o contraseña incorrectos")

        # Generar el token JWT
        access_token = crear_token_acceso(data={"sub": usuario["correo"], "rol": usuario["rol"]})

        # Devolver el token JWT y el rol del usuario
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "rol": usuario["rol"]  # Esto se usará en el frontend para redirigir
        }

    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")
    
# Ruta protegida para obtener información del usuario actual
@router.get("/usuarios/me")
async def leer_usuarios_me(usuario: dict = Depends(obtener_usuario_actual)):
    return {"email": usuario["sub"], "rol": usuario["rol"]}

@router.get("/admin/ruta-protegida", dependencies=[Depends(verificar_admin)])
async def ruta_protegida():
    return {"message": "Solo los admins pueden acceder a esta ruta"}