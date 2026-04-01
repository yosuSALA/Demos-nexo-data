from pydantic import BaseModel

class ModoConfianzaUpdate(BaseModel):
    activo: bool
