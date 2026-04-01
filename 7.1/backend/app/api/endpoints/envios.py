from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.api.deps import get_db, get_current_user
from app.models.user import User, RolEnum
from app.models.envio import Envio, EnvioEstado
from app.services.confianza_service import check_modo_confianza
from app.services.email_service import send_resumen_supervisor
from app.schemas.mapeo_schema import ValidateMappingResponse, ValidarPdfRequest
from app.services.mapping_logic import validate_pdf_mapping

router = APIRouter()

@router.post("/{envio_id}/ejecutar")
def ejecutar_envio(
    envio_id: int, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """
    1. Verifica que el usuario es el creador del envio o un Supervisor/Admin
    2. Si el usuario es Operador: llama check_modo_confianza()
       - Si True: ejecuta directamente, cambia estado a 'enviando'
       - Si False: cambia estado a 'pendiente_aprobacion', notifica al Supervisor
    3. Si el usuario es Supervisor o Admin: ejecuta directamente siempre
    """
    # MOCK SAFETY: Si no hay Base de Datos inyectada por el deps dummy
    if not db:
        return {"msg": f"[DUMMY] Lógica procesada para usuario rol: {current_user.rol.value}. No hay BD real aún."}
    
    envio = db.query(Envio).filter(Envio.id == envio_id).first()
    if not envio:
        raise HTTPException(status_code=404, detail="Envío masivo no encontrado")
        
    # Verificar propiedad del envío
    if envio.creado_por != current_user.id and current_user.rol not in [RolEnum.admin, RolEnum.supervisor]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Operación inválida: No tienes permisos sobre este lote de correos."
        )
        
    # LOGICA OPERADORES DENTRO DE RRHH
    if current_user.rol == RolEnum.operador:
        confianza_habilitada = check_modo_confianza(current_user.id, db)
        
        if confianza_habilitada:
            envio.estado = EnvioEstado.enviando
            envio.modo_confianza_usado = True
            envio.ejecutado_en = datetime.utcnow()
            db.commit()
            
            # TODO: LLAMADA A BACKGROUND TASKS DE ENVÍO DE EMAIL ACA
            # Post-Envío: Supervisor recibe resumen por mail
            send_resumen_supervisor(envio.id, db)
            
            return {
                "msg": "Modo Confianza Validado: Tus correos de nómina están en camino directo.", 
                "estado": envio.estado
            }
        else:
            # Va a la "Bandeja de Entrada" del Supervisor
            envio.estado = EnvioEstado.pendiente_aprobacion
            db.commit()
            # TODO: NOTIFICAR SUPERVISOR PARA QUE DESPACHE
            return {
                "msg": "El envío ha sido encolado para la revisión de un Supervisor.", 
                "estado": envio.estado
            }
            
    # LÓGICA SUPERVISORES Y ADMINS (Autopases)
    envio.estado = EnvioEstado.enviando
    envio.aprobado_por = current_user.id
    envio.ejecutado_en = datetime.utcnow()
    db.commit()
    
    # TODO: LLAMADA A BACKGROUND TASKS ACA
    return {"msg": "Autoridad Verificada: El envío de nómina ha comenzado.", "estado": envio.estado}


@router.post("/{envio_id}/validar", response_model=ValidateMappingResponse)
def validar_mapeo_pdfs(
    envio_id: int, 
    payload: ValidarPdfRequest,
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """
    Recibe los nombres de los PDFs y valida su cruce numérico con la
    cédula de los destinatarios. Retorna el resultado completo del motor.
    """
    return validate_pdf_mapping(envio_id, payload.archivos_subidos, payload.grupo_id, db)


@router.post("/{envio_id}/preview-mapeo")
def obtener_preview_mapeo(
    envio_id: int, 
    payload: ValidarPdfRequest,
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """
    Formatea la validación de mapeo explícitamente para el Frontend de React.
    Genera tabla: [Empleado, Cedula, PDF asignado, Estado, Advertencias]
    """
    validacion_completa = validate_pdf_mapping(envio_id, payload.archivos_subidos, payload.grupo_id, db)
    
    tabla_visual = []
    
    for match in validacion_completa.matches:
        tabla_visual.append({
            "Empleado": match.empleado_nombre,
            "Cedula": match.cedula,
            "PDF_Asignado": match.pdf_filename,
            "Estado": match.status,
            "Advertencias": ", ".join(match.advertencias) if match.advertencias else "Ninguna"
        })
        
    for error_pdf in validacion_completa.sin_pdf:
        tabla_visual.append({
            "Empleado": error_pdf.empleado_nombre,
            "Cedula": error_pdf.cedula,
            "PDF_Asignado": "FALTANTE",
            "Estado": "error",
            "Advertencias": "Ningún PDF con esta cédula fue subido"
        })
        
    for error_emp in validacion_completa.sin_empleado:
        tabla_visual.append({
            "Empleado": "DESCONOCIDO",
            "Cedula": "DESCONOCIDO",
            "PDF_Asignado": error_emp.pdf_filename,
            "Estado": "error",
            "Advertencias": "PDF no matchea con ninguna cédula del grupo"
        })
        
    return {
        "puede_ejecutar": validacion_completa.puede_ejecutar,
        "preview": tabla_visual
    }
