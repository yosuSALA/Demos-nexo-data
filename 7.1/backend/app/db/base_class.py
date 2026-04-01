from typing import Any
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import declarative_base

class CustomBase:
    id: Any
    __name__: str
    
    # Parsea el nombre de tabla automáticamente para todas las clases
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

Base = declarative_base(cls=CustomBase)
