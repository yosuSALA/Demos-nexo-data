from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.endpoints import envios, usuarios, configuracion, auth, grupos, empleados, admin
from app.db.session import engine
from app.db.base_class import Base

# Modelos — necesarios para que create_all los registre
import app.models.user
import app.models.empleado
import app.models.envio
import app.models.config

# Crear tablas que no existan
Base.metadata.create_all(bind=engine)

# Migración ligera: agrega columnas SMTP a config_global si ya existía la tabla
# (SQLite no las añade automáticamente con create_all en tablas existentes)
_smtp_cols = {
    "smtp_host":      "VARCHAR(255)",
    "smtp_port":      "INTEGER",
    "smtp_user":      "VARCHAR(255)",
    "smtp_password":  "VARCHAR(255)",
    "smtp_use_tls":   "BOOLEAN DEFAULT 0",
    "smtp_remitente": "VARCHAR(255)",
}
with engine.connect() as _conn:
    for _col, _tipo in _smtp_cols.items():
        try:
            _conn.execute(text(f"ALTER TABLE config_global ADD COLUMN {_col} {_tipo}"))
            _conn.commit()
        except Exception:
            pass  # La columna ya existe

app = FastAPI(title="Nexo Data Demo API", version="2.0.0")

# CORS para React (Vite puerto 5173 / 5174)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción especificar el origen exacto
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(envios.router,        prefix="/api/envios",        tags=["envios"])
app.include_router(usuarios.router,      prefix="/api/usuarios",      tags=["usuarios"])
app.include_router(configuracion.router, prefix="/api/configuracion", tags=["configuracion"])
app.include_router(auth.router,          prefix="/api/auth",          tags=["auth"])
app.include_router(grupos.router,        prefix="/api/grupos",        tags=["grupos"])
app.include_router(empleados.router,     prefix="/api/empleados",     tags=["empleados"])
app.include_router(admin.router,         prefix="/api/admin",         tags=["admin"])

@app.get("/")
def read_root():
    return {"message": "Nexo RRHH API v2.0 — Demo 7 Final activa."}
