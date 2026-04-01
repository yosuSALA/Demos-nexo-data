from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from app.api.deps import get_db, get_current_user, get_current_admin, get_current_admin_or_supervisor
from app.models.empleado import Grupo, OperadorGrupo
from app.models.user import User, RolEnum

router = APIRouter()

class GrupoCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

class GrupoResponse(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str]
    class Config:
        from_attributes = True

class AsignarRequest(BaseModel):
    user_id: int  # Cualquier usuario (operador, supervisor, admin)

class MiembroResponse(BaseModel):
    id: int
    nombre: str
    email: str
    rol: str
    class Config:
        from_attributes = True

# ── CRUD GRUPOS (Solo Admin) ───────────────────────────────

@router.post("/", response_model=GrupoResponse)
def create_grupo(payload: GrupoCreate, db: Session = Depends(get_db),
                 current_admin: User = Depends(get_current_admin)):
    g = Grupo(nombre=payload.nombre, descripcion=payload.descripcion, created_by=current_admin.id)
    db.add(g); db.commit(); db.refresh(g)
    return g

@router.get("/", response_model=List[GrupoResponse])
def get_grupos(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Grupo).all()

@router.patch("/{grupo_id}", response_model=GrupoResponse)
def editar_grupo(grupo_id: int, payload: GrupoCreate, db: Session = Depends(get_db),
                 current_admin: User = Depends(get_current_admin)):
    g = db.query(Grupo).filter(Grupo.id == grupo_id).first()
    if not g: raise HTTPException(status_code=404, detail="Grupo no encontrado.")
    g.nombre = payload.nombre
    if payload.descripcion is not None: g.descripcion = payload.descripcion
    db.commit(); db.refresh(g)
    return g

@router.delete("/{grupo_id}")
def eliminar_grupo(grupo_id: int, db: Session = Depends(get_db),
                   current_admin: User = Depends(get_current_admin)):
    g = db.query(Grupo).filter(Grupo.id == grupo_id).first()
    if not g: raise HTTPException(status_code=404, detail="Grupo no encontrado.")
    db.delete(g); db.commit()
    return {"msg": f"Grupo '{g.nombre}' eliminado correctamente."}

# ── GRUPOS DEL USUARIO ACTUAL (filtro por rol) ─────────────

@router.get("/mis-grupos", response_model=List[GrupoResponse])
def get_mis_grupos(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Operador: solo sus grupos asignados. Admin/Supervisor: todos."""
    if current_user.rol == RolEnum.operador:
        ids = [a.grupo_id for a in db.query(OperadorGrupo).filter(
            OperadorGrupo.user_id == current_user.id).all()]
        return db.query(Grupo).filter(Grupo.id.in_(ids)).all() if ids else []
    return db.query(Grupo).all()

# ── MIEMBROS DE UN GRUPO ────────────────────────────────────

@router.get("/{grupo_id}/miembros", response_model=List[MiembroResponse])
def get_miembros(grupo_id: int, db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    """Devuelve todos los usuarios asignados a este grupo."""
    grupo = db.query(Grupo).filter(Grupo.id == grupo_id).first()
    if not grupo:
        raise HTTPException(status_code=404, detail="Grupo no encontrado.")
    asignaciones = db.query(OperadorGrupo).filter(OperadorGrupo.grupo_id == grupo_id).all()
    user_ids = [a.user_id for a in asignaciones]
    if not user_ids:
        return []
    return db.query(User).filter(User.id.in_(user_ids)).all()

# ── ASIGNAR / DESASIGNAR USUARIOS A GRUPO (Admin y Supervisor) ─────

@router.post("/{grupo_id}/asignar")
def asignar_usuario_a_grupo(grupo_id: int, payload: AsignarRequest,
                             db: Session = Depends(get_db),
                             current_user: User = Depends(get_current_admin_or_supervisor)):
    """Asigna un usuario a un grupo. Admin y Supervisor."""
    grupo = db.query(Grupo).filter(Grupo.id == grupo_id).first()
    if not grupo:
        raise HTTPException(status_code=404, detail="Grupo no encontrado.")
    usuario = db.query(User).filter(User.id == payload.user_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    ya = db.query(OperadorGrupo).filter(
        OperadorGrupo.user_id == payload.user_id,
        OperadorGrupo.grupo_id == grupo_id).first()
    if ya:
        raise HTTPException(status_code=400, detail=f"'{usuario.nombre}' ya está en este grupo.")
    db.add(OperadorGrupo(user_id=payload.user_id, grupo_id=grupo_id))
    db.commit()
    return {"msg": f"'{usuario.nombre}' ({usuario.rol.value}) asignado al grupo '{grupo.nombre}'."}

@router.delete("/{grupo_id}/desasignar/{user_id}")
def desasignar_usuario(grupo_id: int, user_id: int, db: Session = Depends(get_db),
                       current_user: User = Depends(get_current_admin_or_supervisor)):
    """Elimina la asignación de un usuario de un grupo. Admin y Supervisor."""
    a = db.query(OperadorGrupo).filter(
        OperadorGrupo.user_id == user_id,
        OperadorGrupo.grupo_id == grupo_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Asignación no encontrada.")
    db.delete(a); db.commit()
    return {"msg": "Usuario desasignado del grupo correctamente."}
