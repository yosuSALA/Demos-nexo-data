import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, Enum as SQLEnum, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.db.base_class import Base

class EnvioEstado(str, enum.Enum):
    borrador = "borrador"
    pendiente_aprobacion = "pendiente_aprobacion"
    aprobado = "aprobado"
    enviando = "enviando"
    completado = "completado"
    fallido = "fallido"

class LogEstado(str, enum.Enum):
    ok = "ok"
    fallo = "fallo"

class PlantillaEmail(Base):
    __tablename__ = "plantilla_email"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    asunto = Column(String(255), nullable=False)
    cuerpo_html = Column(Text, nullable=False)
    
    envios = relationship("Envio", back_populates="plantilla")

class Envio(Base):
    __tablename__ = "envio"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(255), nullable=False)
    creado_por = Column(Integer, ForeignKey("usuario.id", ondelete="SET NULL"), nullable=True)
    aprobado_por = Column(Integer, ForeignKey("usuario.id", ondelete="SET NULL"), nullable=True)
    grupo_id = Column(Integer, ForeignKey("grupo.id", ondelete="SET NULL"), nullable=True)
    plantilla_id = Column(Integer, ForeignKey("plantilla_email.id", ondelete="SET NULL"), nullable=True)

    estado = Column(SQLEnum(EnvioEstado), default=EnvioEstado.borrador)
    modo_confianza_usado = Column(Boolean, default=False)
    
    programado_para = Column(DateTime, nullable=True)
    ejecutado_en = Column(DateTime, nullable=True)
    
    total = Column(Integer, default=0)
    enviados_ok = Column(Integer, default=0)
    enviados_fallo = Column(Integer, default=0)

    creador = relationship("User", foreign_keys=[creado_por], back_populates="envios_creados")
    aprobador = relationship("User", foreign_keys=[aprobado_por])
    grupo = relationship("Grupo", back_populates="envios")
    plantilla = relationship("PlantillaEmail", back_populates="envios")
    logs = relationship("LogEnvio", back_populates="envio", cascade="all, delete-orphan")

class LogEnvio(Base):
    __tablename__ = "log_envio"

    id = Column(Integer, primary_key=True, index=True)
    envio_id = Column(Integer, ForeignKey("envio.id", ondelete="CASCADE"), nullable=False)
    empleado_id = Column(Integer, ForeignKey("empleado.id", ondelete="SET NULL"), nullable=True)
    
    pdf_filename = Column(String(255), nullable=True)
    estado = Column(SQLEnum(LogEstado), nullable=False)
    error_message = Column(Text, nullable=True)
    enviado_en = Column(DateTime, default=datetime.utcnow)

    envio = relationship("Envio", back_populates="logs")
    empleado = relationship("Empleado", back_populates="logs_envio")
