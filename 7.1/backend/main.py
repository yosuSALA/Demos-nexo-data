from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# Forzando recarga de servidor para limpiar cache de db (auto-reload)
from app.api.endpoints import envios, usuarios, configuracion, auth, grupos, empleados
from app.db.session import engine
from app.db.base_class import Base

# Modelos
import app.models.user
import app.models.empleado
import app.models.envio
import app.models.config

# Crear Tablas
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Nexo Data Demo API", version="1.0.0")

# Habilitar CORS para que React (Vite en puerto 5173 / puerto dinámico) pueda conectarse
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En producción se debería especificar el origen exacto
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir los endpoints que ya habíamos generado
app.include_router(envios.router, prefix="/api/envios", tags=["envios"])
app.include_router(usuarios.router, prefix="/api/usuarios", tags=["usuarios"])
app.include_router(configuracion.router, prefix="/api/configuracion", tags=["configuracion"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(grupos.router, prefix="/api/grupos", tags=["grupos"])
app.include_router(empleados.router, prefix="/api/empleados", tags=["empleados"])

@app.get("/")
def read_root():
    return {"message": "¡API de Nexo Data Demo (RRHH) está funcionando perfectamente!"}
