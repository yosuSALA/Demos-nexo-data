from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

from app.api.deps import get_db, get_current_admin, get_current_admin_or_supervisor, get_current_user
from app.models.user import User, ConfianzaConfig, RolEnum
from app.schemas.confianza_schema import ModoConfianzaUpdate

router = APIRouter()

class UserResponse(BaseModel):
    id: int
    nombre: str
    email: str
    rol: str
    activo: bool

    class Config:
        from_attributes = True

class UserDestinatarioResponse(BaseModel):
    id: int
    nombre: str
    email: str

    class Config:
        from_attributes = True

class CambiarRolRequest(BaseModel):
    rol: str

# --- LISTADO DE USUARIOS (Solo Admin) ---

@router.get("/", response_model=List[UserResponse])
def get_usuarios(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_or_supervisor)
):
    """Lista todos los usuarios del sistema. Admin y Supervisor (lectura)."""
    return db.query(User).all()

@router.get("/operadores", response_model=List[UserResponse])
def get_operadores(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_or_supervisor)
):
    """Lista solo los Operadores. Admin y Supervisor."""
    return db.query(User).filter(User.rol == RolEnum.operador).all()

@router.get("/para-envio", response_model=List[UserDestinatarioResponse])
def get_para_envio(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista todos los usuarios activos como posibles destinatarios. Cualquier usuario logueado."""
    return db.query(User).filter(User.activo == True).all()


# --- CAMBIO DE ROL (Solo Admin) ---

@router.patch("/{user_id}/rol")
def cambiar_rol_usuario(
    user_id: int,
    payload: CambiarRolRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Cambia el rol de un usuario. Solo Admin."""
    if payload.rol not in ["admin", "supervisor", "operador"]:
        raise HTTPException(status_code=400, detail="Rol inválido. Use: admin, supervisor u operador.")
    
    usuario = db.query(User).filter(User.id == user_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    if usuario.id == current_admin.id:
        raise HTTPException(status_code=400, detail="No puedes cambiar tu propio rol.")
    
    usuario.rol = RolEnum(payload.rol)
    db.commit()
    return {"msg": f"Rol de '{usuario.nombre}' cambiado a '{payload.rol}' correctamente."}

# --- ACTIVAR/DESACTIVAR MODO CONFIANZA (Admin y Supervisor) ---

@router.patch("/{user_id}/modo-confianza")
def set_modo_confianza_individual(
    user_id: int,
    payload: ModoConfianzaUpdate,
    current_admin_sup: User = Depends(get_current_admin_or_supervisor),
    db: Session = Depends(get_db)
):
    """
    Controla el acceso de 'Confianza' para Operadores Individuales.
    Solo accesible por Admin y Supervisor.
    """
    operador = db.query(User).filter(User.id == user_id, User.rol == RolEnum.operador).first()
    if not operador:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Error 404: Empleado no existe o no tiene rango de Operador."
        )

    confianza = db.query(ConfianzaConfig).filter(ConfianzaConfig.operador_user_id == user_id).first()
    now = datetime.utcnow()

    if not confianza:
        confianza = ConfianzaConfig(
            operador_user_id=user_id,
            activado_por=current_admin_sup.id,
            activo=payload.activo,
            activado_en=now if payload.activo else None,
            desactivado_en=None if payload.activo else now
        )
        db.add(confianza)
    else:
        confianza.activo = payload.activo
        confianza.activado_por = current_admin_sup.id
        if payload.activo:
            confianza.activado_en = now
        else:
            confianza.desactivado_en = now

    db.commit()
    return {"msg": f"El Modo Confianza de RRHH para {operador.nombre} ha cambiado a: {payload.activo}"}
