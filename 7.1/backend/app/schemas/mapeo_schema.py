from pydantic import BaseModel
from typing import List, Optional

class MatchItem(BaseModel):
    empleado_nombre: str
    cedula: str
    pdf_filename: str
    status: str = "ok" # Puede ser 'ok' o 'advertencia'
    advertencias: Optional[List[str]] = []

class SinPdfItem(BaseModel):
    empleado_nombre: str
    cedula: str
    
class SinEmpleadoItem(BaseModel):
    pdf_filename: str

class ValidateMappingResponse(BaseModel):
    matches: List[MatchItem]
    sin_pdf: List[SinPdfItem]
    sin_empleado: List[SinEmpleadoItem]
    puede_ejecutar: bool

class ValidarPdfRequest(BaseModel):
    archivos_subidos: List[str]
    grupo_id: int
