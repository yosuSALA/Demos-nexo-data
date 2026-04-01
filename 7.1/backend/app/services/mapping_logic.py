import re
from typing import List
from sqlalchemy.orm import Session
from app.models.empleado import Empleado, Grupo
from app.schemas.mapeo_schema import (
    ValidateMappingResponse, MatchItem, SinPdfItem, SinEmpleadoItem
)

# Regex simple para emails
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

def is_valid_email(email: str) -> bool:
    if not email:
        return False
    return bool(EMAIL_REGEX.match(email))

def validate_pdf_mapping(envio_id: int, archivos_subidos: List[str], grupo_id: int, db: Session) -> ValidateMappingResponse:
    # MOCK SAFETY para evitar crashes si corremos sin DB configurada aún
    if not db:
        # Devolvemos un mock forzoso (Ningún pdf matchea con base vacía)
        errs = [SinEmpleadoItem(pdf_filename=f) for f in archivos_subidos]
        return ValidateMappingResponse(
            matches=[], sin_pdf=[], sin_empleado=errs, puede_ejecutar=False
        )

    # 1. Recuperar los empleados asociados al grupo_id
    grupo = db.query(Grupo).filter(Grupo.id == grupo_id).first()
    
    # 2. Convertir la lista en un SET para eliminar aciertos iterativamente
    archivos_pendientes = set(archivos_subidos)

    matches: List[MatchItem] = []
    sin_pdf: List[SinPdfItem] = []
    sin_empleado: List[SinEmpleadoItem] = []

    if grupo:
        for emp in grupo.empleados:
            found_pdf = None
            
            # REGLA CENTRAL HR: Buscar la subcadena (cédula) en el nombre de los PDFs
            for archivo in archivos_pendientes:
                if emp.cedula in archivo:
                    found_pdf = archivo
                    break
            
            if found_pdf:
                # Retirarlo de los pendientes asegura mapeo 1 a 1 de primer cruce
                archivos_pendientes.remove(found_pdf)
                
                # Validación de ADVERTENCIA (no bloquea el flujo principal, solo previene error)
                warnings = []
                status = "ok"
                if not is_valid_email(emp.email):
                    status = "advertencia"
                    warnings.append(f"Email '{emp.email}' inválido/en blanco.")
                    
                matches.append(MatchItem(
                    empleado_nombre=f"{emp.nombre} {emp.apellido}",
                    cedula=emp.cedula,
                    pdf_filename=found_pdf,
                    status=status,
                    advertencias=warnings
                ))
            else:
                # Si no se encontró un PDF con esta cédula, el empleado queda huerfano
                sin_pdf.append(SinPdfItem(
                    empleado_nombre=f"{emp.nombre} {emp.apellido}",
                    cedula=emp.cedula
                ))

    # 3. Tras iterar Nómina, los PDFs sobrantes indican errores de subida
    for arch in archivos_pendientes:
        sin_empleado.append(SinEmpleadoItem(pdf_filename=arch))

    # 4. REGLA CRÍTICA: Bloquear el puede_ejecutar si no es mapeo perfecto
    puede_ejecutar = (len(sin_pdf) == 0 and len(sin_empleado) == 0)

    return ValidateMappingResponse(
        matches=matches,
        sin_pdf=sin_pdf,
        sin_empleado=sin_empleado,
        puede_ejecutar=puede_ejecutar
    )
