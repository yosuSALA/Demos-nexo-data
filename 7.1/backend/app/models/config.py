from sqlalchemy import Column, Integer, Boolean, String
from app.db.base_class import Base

class ConfigGlobal(Base):
    __tablename__ = "config_global"

    id = Column(Integer, primary_key=True, index=True)
    modo_confianza_global = Column(Boolean, default=False)

    # Configuración SMTP para envío real de correos
    smtp_host = Column(String(255), nullable=True)
    smtp_port = Column(Integer, nullable=True)
    smtp_user = Column(String(255), nullable=True)
    smtp_password = Column(String(255), nullable=True)
    smtp_use_tls = Column(Boolean, default=False)
    smtp_remitente = Column(String(255), nullable=True)
