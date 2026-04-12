from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.api.deps import get_db, get_current_admin
from app.models.config import ConfigGlobal
from app.models.user import User
from app.schemas.confianza_schema import ModoConfianzaUpdate

router = APIRouter()

# ── Schemas SMTP ─────────────────────────────────────────────────────────────

class SmtpConfigUpdate(BaseModel):
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: Optional[bool] = None
    smtp_remitente: Optional[str] = None

class SmtpConfigResponse(BaseModel):
    smtp_host: str
    smtp_port: int
    smtp_user: Optional[str]
    smtp_use_tls: bool
    smtp_remitente: str

# ── GET /smtp ─────────────────────────────────────────────────────────────────

@router.get("/smtp", response_model=SmtpConfigResponse)
def get_smtp_config(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Devuelve la configuración SMTP actual (sin exponer la contraseña)."""
    config = db.query(ConfigGlobal).first()
    if config and config.smtp_host:
        return SmtpConfigResponse(
            smtp_host=config.smtp_host,
            smtp_port=config.smtp_port or 1025,
            smtp_user=config.smtp_user,
            smtp_use_tls=config.smtp_use_tls or False,
            smtp_remitente=config.smtp_remitente or "rrhh@nexodata-demo.com",
        )
    return SmtpConfigResponse(
        smtp_host="localhost", smtp_port=1025,
        smtp_user=None, smtp_use_tls=False,
        smtp_remitente="rrhh@nexodata-demo.com",
    )

# ── PATCH /smtp ───────────────────────────────────────────────────────────────

@router.patch("/smtp")
def update_smtp_config(
    payload: SmtpConfigUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Actualiza la configuración SMTP. Solo Admin."""
    config = db.query(ConfigGlobal).first()
    if not config:
        config = ConfigGlobal()
        db.add(config)
    for field, val in payload.model_dump(exclude_none=True).items():
        setattr(config, field, val)
    db.commit()
    return {"msg": "Configuración SMTP actualizada correctamente."}

# ── PATCH /modo-confianza-global ──────────────────────────────────────────────

@router.patch("/modo-confianza-global")
def set_modo_confianza_global(
    payload: ModoConfianzaUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Administra la opción que vuelve el Modo Confianza global 
    en momentos pico. Exclusivo para Admins.
    """
    # MOCK SAFETY
    if not db:
        return {"msg": f"[{admin.nombre} / DUMMY DB] Flag Global de Confianza modificado satisfactoriamente a {payload.activo}."}

    config = db.query(ConfigGlobal).first()
    if not config:
        config = ConfigGlobal(modo_confianza_global=payload.activo)
        db.add(config)
    else:
        config.modo_confianza_global = payload.activo

    db.commit()
    estado_str = "ACTIVADO (Saltará las aprobaciones)" if payload.activo else "DESACTIVADO (Operadores volverán a la revisión)"
    
    return {"msg": f"El Modo Confianza Global en la empresa está ahora {estado_str}"}
