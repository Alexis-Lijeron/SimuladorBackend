from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import usuario, doctor, pago, rol

app = FastAPI()

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir las rutas
app.include_router(usuario.router)
app.include_router(doctor.router)
app.include_router(pago.router)
app.include_router(rol.router)

@app.get("/")
def read_root():
    return {"message": "¡Conectado a MongoDB!"}
