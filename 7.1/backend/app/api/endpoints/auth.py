from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.models.user import User, RolEnum
from app.core.security import get_password_hash, verify_password, create_access_token
from pydantic import BaseModel, EmailStr

router = APIRouter()

class RegisterUserRequest(BaseModel):
    nombre: str
    email: EmailStr
    password: str
    rol: RolEnum

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/register")
def register_user(payload: RegisterUserRequest, db: Session = Depends(get_db)):
    if not db:
        return {"msg": "No hay Base de Datos conectada"}
    
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Este correo electrónico ya está registrado.")
    
    nuevo_user = User(
        nombre=payload.nombre,
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        rol=payload.rol
    )
    db.add(nuevo_user)
    db.commit()
    db.refresh(nuevo_user)
    
    return {"msg": f"Usuario {nuevo_user.nombre} registrado como {nuevo_user.rol.value}."}

@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    if not db:
        return {"msg": "No hay Base de Datos conectada"}
        
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
        
    access_token = create_access_token(data={"sub": str(user.id), "rol": user.rol.value})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "usuario": {
            "id": user.id,
            "nombre": user.nombre,
            "email": user.email,
            "rol": user.rol.value
        }
    }
