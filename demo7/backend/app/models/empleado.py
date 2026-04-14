import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Enum as SQLEnum, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base_class import Base

class EmpleadoEstado(str, enum.Enum):
    activo = "activo"
    inactivo = "inactivo"
    prueba = "prueba"

class Grupo(Base):
    __tablename__ = "grupo"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False)
    descripcion = Column(String(255), nullable=True)
    created_by = Column(Integer, ForeignKey("usuario.id", ondelete="SET NULL"), nullable=True)

    creador = relationship("User", back_populates="grupos_propios")
    empleados = relationship("Empleado", back_populates="grupo", cascade="all, delete-orphan")
    asignaciones_operadores = relationship("OperadorGrupo", back_populates="grupo", cascade="all, delete-orphan")
    envios = relationship("Envio", back_populates="grupo")


class Empleado(Base):
    __tablename__ = "empleado"

    id = Column(Integer, primary_key=True, index=True)
    cedula = Column(String(20), unique=True, index=True, nullable=False) # Clave indispensable para el mapeo PDF
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    email = Column(String(255), nullable=True)
    departamento = Column(String(100), nullable=True)
    cargo = Column(String(100), nullable=True)
    estado = Column(SQLEnum(EmpleadoEstado), default=EmpleadoEstado.activo)
    grupo_id = Column(Integer, ForeignKey("grupo.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    grupo = relationship("Grupo", back_populates="empleados")
    logs_envio = relationship("LogEnvio", back_populates="empleado")


class OperadorGrupo(Base):
    __tablename__ = "operador_grupo"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False)
    grupo_id = Column(Integer, ForeignKey("grupo.id", ondelete="CASCADE"), nullable=False)

    operador = relationship("User", back_populates="grupos_asignados")
    grupo = relationship("Grupo", back_populates="asignaciones_operadores")
