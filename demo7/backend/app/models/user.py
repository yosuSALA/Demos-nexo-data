import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, Enum as SQLEnum, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.db.base_class import Base

class RolEnum(str, enum.Enum):
    admin = "admin"
    supervisor = "supervisor"
    operador = "operador"

class ProveedorOAuth(str, enum.Enum):
    gmail = "gmail"
    outlook = "outlook"

class User(Base):
    __tablename__ = "usuario" # Sobrescribe el default por claridad en español si es necesario (el default sería 'user')

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    nombre = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    rol = Column(SQLEnum(RolEnum), nullable=False)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relaciones - Usando strings para evitar importaciones circulares inmediatas
    oauth_tokens = relationship("OAuthToken", back_populates="user", cascade="all, delete-orphan")
    confianza_config = relationship("ConfianzaConfig", foreign_keys="[ConfianzaConfig.operador_user_id]", back_populates="operador", uselist=False)
    grupos_asignados = relationship("OperadorGrupo", back_populates="operador", cascade="all, delete-orphan")
    grupos_propios = relationship("Grupo", back_populates="creador")
    envios_creados = relationship("Envio", foreign_keys="[Envio.creado_por]", back_populates="creador")

class OAuthToken(Base):
    __tablename__ = "oauth_token"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False)
    proveedor = Column(SQLEnum(ProveedorOAuth), nullable=False)
    access_token_enc = Column(Text, nullable=False)
    refresh_token_enc = Column(Text, nullable=False)
    expires_at = Column(DateTime, nullable=False)

    user = relationship("User", back_populates="oauth_tokens")

class ConfianzaConfig(Base):
    __tablename__ = "confianza_config"

    id = Column(Integer, primary_key=True, index=True)
    operador_user_id = Column(Integer, ForeignKey("usuario.id", ondelete="CASCADE"), unique=True, nullable=False)
    activado_por = Column(Integer, ForeignKey("usuario.id", ondelete="SET NULL"), nullable=True)
    activo = Column(Boolean, default=False)
    activado_en = Column(DateTime, nullable=True)
    desactivado_en = Column(DateTime, nullable=True)

    operador = relationship("User", foreign_keys=[operador_user_id], back_populates="confianza_config")
    autorizador = relationship("User", foreign_keys=[activado_por])
