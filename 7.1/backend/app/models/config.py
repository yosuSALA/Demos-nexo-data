from sqlalchemy import Column, Integer, Boolean
from app.db.base_class import Base

class ConfigGlobal(Base):
    __tablename__ = "config_global"

    id = Column(Integer, primary_key=True, index=True)
    modo_confianza_global = Column(Boolean, default=False)
