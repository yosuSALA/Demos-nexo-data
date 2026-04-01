from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_admin
from app.models.config import ConfigGlobal
from app.models.user import User
from app.schemas.confianza_schema import ModoConfianzaUpdate

router = APIRouter()

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
