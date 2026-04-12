from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List

from app.api.deps import get_db, get_current_user
from app.models.user import User, RolEnum
from app.models.envio import Envio, EnvioEstado
from app.models.empleado import Grupo
from app.services.confianza_service import check_modo_confianza
from app.services.email_service import send_batch, send_resumen_supervisor, UPLOADS_DIR
from app.schemas.mapeo_schema import ValidateMappingResponse, ValidarPdfRequest
from app.services.mapping_logic import validate_pdf_mapping

router = APIRouter()

# ── Schemas ─────────────────────────────────────────────────────────────────

class EnvioCreate(BaseModel):
    nombre: str
    grupo_id: int
    plantilla_id: Optional[int] = None

class EnvioResponse(BaseModel):
    id: int
    nombre: str
    grupo_id: Optional[int]
    estado: str
    total: int
    enviados_ok: int
    enviados_fallo: int
    creado_por: Optional[int]
    ejecutado_en: Optional[datetime]

    class Config:
        from_attributes = True

# ── POST / — crear envío ────────────────────────────────────────────────────

@router.post("/", response_model=EnvioResponse, status_code=201)
def crear_envio(
    payload: EnvioCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Crea un nuevo lote de envío en estado 'borrador'."""
    if not db.query(Grupo).filter(Grupo.id == payload.grupo_id).first():
        raise HTTPException(status_code=404, detail="Grupo no encontrado.")

    envio = Envio(
        nombre=payload.nombre,
        grupo_id=payload.grupo_id,
        plantilla_id=payload.plantilla_id,
        creado_por=current_user.id,
        estado=EnvioEstado.borrador,
    )
    db.add(envio)
    db.commit()
    db.refresh(envio)
    return envio

# ── GET / — listar envíos ───────────────────────────────────────────────────

@router.get("/", response_model=List[EnvioResponse])
def listar_envios(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lista envíos. Operador solo ve los suyos; Admin/Supervisor ve todos."""
    q = db.query(Envio)
    if current_user.rol == RolEnum.operador:
        q = q.filter(Envio.creado_por == current_user.id)
    return q.order_by(Envio.id.desc()).all()

# ── POST /{id}/upload-pdfs — subir PDFs del lote ───────────────────────────

@router.post("/{envio_id}/upload-pdfs")
async def upload_pdfs(
    envio_id: int,
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Recibe los PDFs del lote y los almacena en uploads/{envio_id}/.
    El nombre de cada PDF debe contener la cédula del empleado para el
    motor de mapeo automático (ej: nomina_0901234567_marzo.pdf).
    """
    envio = db.query(Envio).filter(Envio.id == envio_id).first()
    if not envio:
        raise HTTPException(status_code=404, detail="Envío no encontrado.")
    if envio.creado_por != current_user.id and current_user.rol not in [RolEnum.admin, RolEnum.supervisor]:
        raise HTTPException(status_code=403, detail="Sin permisos sobre este envío.")

    destino = UPLOADS_DIR / str(envio_id)
    destino.mkdir(parents=True, exist_ok=True)

    nombres = []
    for f in files:
        ruta = destino / f.filename
        contenido = await f.read()
        ruta.write_bytes(contenido)
        nombres.append(f.filename)

    return {"msg": f"{len(nombres)} PDF(s) subidos correctamente.", "archivos": nombres}

# ── POST /{id}/ejecutar ─────────────────────────────────────────────────────

@router.post("/{envio_id}/ejecutar")
def ejecutar_envio(
    envio_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    1. Verifica permisos del usuario sobre el envío.
    2. Si Operador: evalúa Modo Confianza.
       - Con Confianza → envía directamente vía SMTP.
       - Sin Confianza → encola para aprobación del Supervisor.
    3. Admin / Supervisor → envía directamente siempre.
    """
    if not db:
        return {"msg": f"[DUMMY] Lógica procesada para rol: {current_user.rol.value}"}

    envio = db.query(Envio).filter(Envio.id == envio_id).first()
    if not envio:
        raise HTTPException(status_code=404, detail="Envío masivo no encontrado.")

    if envio.creado_por != current_user.id and current_user.rol not in [RolEnum.admin, RolEnum.supervisor]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos sobre este lote de correos."
        )

    # ── Operador ──────────────────────────────────────────────────────────
    if current_user.rol == RolEnum.operador:
        if check_modo_confianza(current_user.id, db):
            envio.estado = EnvioEstado.enviando
            envio.modo_confianza_usado = True
            db.commit()

            send_batch(envio_id, db)
            send_resumen_supervisor(envio_id, db)

            db.refresh(envio)
            return {
                "msg": "Modo Confianza Validado: tus correos de nómina fueron despachados.",
                "estado": envio.estado.value,
                "enviados_ok": envio.enviados_ok,
                "enviados_fallo": envio.enviados_fallo,
                "total": envio.total,
                "envio_id": envio_id,
            }
        else:
            envio.estado = EnvioEstado.pendiente_aprobacion
            db.commit()
            return {
                "msg": "El envío fue encolado y el Supervisor fue notificado para revisar.",
                "estado": EnvioEstado.pendiente_aprobacion.value,
                "envio_id": envio_id,
            }

    # ── Admin / Supervisor ────────────────────────────────────────────────
    envio.estado      = EnvioEstado.enviando
    envio.aprobado_por = current_user.id
    db.commit()

    send_batch(envio_id, db)
    send_resumen_supervisor(envio_id, db)

    db.refresh(envio)
    return {
        "msg": "Autoridad verificada: el envío de nómina fue completado.",
        "estado": envio.estado.value,
        "enviados_ok": envio.enviados_ok,
        "enviados_fallo": envio.enviados_fallo,
        "total": envio.total,
        "envio_id": envio_id,
    }


# ── POST /{id}/validar — motor de mapeo PDF ─────────────────────────────────

@router.post("/{envio_id}/validar", response_model=ValidateMappingResponse)
def validar_mapeo_pdfs(
    envio_id: int,
    payload: ValidarPdfRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Recibe los nombres de los PDFs y valida su cruce numérico con la
    cédula de los destinatarios. Retorna el resultado completo del motor.
    """
    return validate_pdf_mapping(envio_id, payload.archivos_subidos, payload.grupo_id, db)


# ── POST /{id}/preview-mapeo ─────────────────────────────────────────────────

@router.post("/{envio_id}/preview-mapeo")
def obtener_preview_mapeo(
    envio_id: int,
    payload: ValidarPdfRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Formatea la validación de mapeo para el Frontend de React.
    Genera tabla: [Empleado, Cedula, PDF asignado, Estado, Advertencias]
    """
    validacion = validate_pdf_mapping(envio_id, payload.archivos_subidos, payload.grupo_id, db)

    tabla_visual = []
    for match in validacion.matches:
        tabla_visual.append({
            "Empleado":      match.empleado_nombre,
            "Cedula":        match.cedula,
            "PDF_Asignado":  match.pdf_filename,
            "Estado":        match.status,
            "Advertencias":  ", ".join(match.advertencias) if match.advertencias else "Ninguna",
        })
    for sin_pdf in validacion.sin_pdf:
        tabla_visual.append({
            "Empleado": sin_pdf.empleado_nombre, "Cedula": sin_pdf.cedula,
            "PDF_Asignado": "FALTANTE", "Estado": "error",
            "Advertencias": "Ningún PDF con esta cédula fue subido",
        })
    for sin_emp in validacion.sin_empleado:
        tabla_visual.append({
            "Empleado": "DESCONOCIDO", "Cedula": "DESCONOCIDO",
            "PDF_Asignado": sin_emp.pdf_filename, "Estado": "error",
            "Advertencias": "PDF no matchea con ninguna cédula del grupo",
        })

    return {"puede_ejecutar": validacion.puede_ejecutar, "preview": tabla_visual}
