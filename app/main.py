from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import cita, estado_simulaciones, simulacion, usuario, doctor, pago, rol,paciente,subir_foto1

app = FastAPI()

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir las rutas
app.include_router(usuario.router)
app.include_router(doctor.router)
app.include_router(pago.router)
app.include_router(rol.router)
app.include_router(paciente.router)
app.include_router(cita.router)
app.include_router(subir_foto1.router)
app.include_router(simulacion.router)
app.include_router(estado_simulaciones.router)
@app.get("/")
def read_root():
    return {"message": "¡Conectado a MongoDB!"}
