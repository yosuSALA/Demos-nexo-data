"""
email_service.py — Servicio de envío SMTP real para Nexo RRHH
=============================================================
Integra la lógica de envío masivo del Demo 7 base (email_bot.py) con la
arquitectura de base de datos de la versión 7.1 (FastAPI + SQLAlchemy).

Modos SMTP soportados (configurable desde /api/configuracion/smtp):
  - LOCAL  : localhost:1025  — servidor de debug sin auth
             Iniciar con: python -m smtpd -c DebuggingServer -n localhost:1025
  - GMAIL  : smtp.gmail.com:587 con TLS y Contraseña de Aplicación
"""

import smtplib
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.envio import Envio, EnvioEstado, LogEnvio, LogEstado
from app.models.config import ConfigGlobal

# Directorio donde se almacenan los PDFs subidos por envío
# Ruta: 7.1/backend/uploads/{envio_id}/ o 7.1/backend/uploads/{grupo_id}/
UPLOADS_DIR = Path(__file__).parent.parent.parent / "uploads"

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# ---------------------------------------------------------------------------
# Config SMTP desde BD
# ---------------------------------------------------------------------------

def _get_smtp_cfg(db: Session) -> dict:
    config = db.query(ConfigGlobal).first()
    if config and config.smtp_host:
        return {
            "host":      config.smtp_host,
            "port":      config.smtp_port or 1025,
            "user":      config.smtp_user,
            "password":  config.smtp_password,
            "use_tls":   config.smtp_use_tls or False,
            "remitente": config.smtp_remitente or "rrhh@nexodata-demo.com",
        }
    # Valores por defecto (modo local / debug)
    return {
        "host": "localhost", "port": 1025,
        "user": None, "password": None,
        "use_tls": False,
        "remitente": "rrhh@nexodata-demo.com",
    }

# ---------------------------------------------------------------------------
# Construcción del correo MIME
# ---------------------------------------------------------------------------

def _construir_correo(
    nombre: str,
    email_destino: str,
    asunto_tpl: str,
    cuerpo_tpl: str,
    remitente: str,
    ruta_pdf: Path = None,
) -> MIMEMultipart:
    mes_actual = datetime.now().strftime("%B %Y")
    vars_map = {"[nombre]": nombre, "[mes]": mes_actual, "[empresa]": "Nexo Data S.A."}

    asunto = asunto_tpl
    cuerpo = cuerpo_tpl
    for var, val in vars_map.items():
        asunto = asunto.replace(var, val)
        cuerpo = cuerpo.replace(var, val)

    msg = MIMEMultipart()
    msg["From"]    = remitente
    msg["To"]      = email_destino
    msg["Subject"] = asunto
    msg.attach(MIMEText(cuerpo, "plain", "utf-8"))

    if ruta_pdf and ruta_pdf.exists():
        with open(ruta_pdf, "rb") as f:
            parte = MIMEBase("application", "octet-stream")
            parte.set_payload(f.read())
        encoders.encode_base64(parte)
        parte.add_header("Content-Disposition", f'attachment; filename="{ruta_pdf.name}"')
        msg.attach(parte)

    return msg

# ---------------------------------------------------------------------------
# Búsqueda de PDF por cédula
# ---------------------------------------------------------------------------

def _buscar_pdf(cedula: str, envio_id: int, grupo_id: int) -> Path | None:
    """
    Busca el PDF del empleado por cédula.
    Busca primero en uploads/{envio_id}/ (PDFs subidos vía wizard).
    Si no existe, busca en uploads/{grupo_id}/ (PDFs del seed de demo).
    """
    for directorio in [UPLOADS_DIR / str(envio_id), UPLOADS_DIR / str(grupo_id)]:
        if directorio.exists():
            for archivo in directorio.iterdir():
                if cedula in archivo.name:
                    return archivo
    return None

# ---------------------------------------------------------------------------
# Envío masivo principal
# ---------------------------------------------------------------------------

def send_batch(envio_id: int, db: Session) -> None:
    """
    Itera todos los empleados activos del grupo del Envio, construye un
    correo personalizado con la plantilla y opcionalmente adjunta el PDF
    correspondiente (buscado por cédula), luego envía vía SMTP.
    Registra cada resultado en LogEnvio y actualiza el Envio en BD.
    """
    envio = db.query(Envio).filter(Envio.id == envio_id).first()
    if not envio:
        return

    if not envio.grupo:
        envio.estado = EnvioEstado.fallido
        db.commit()
        print(f"[EMAIL] Envío {envio_id} sin grupo asignado. Marcado como fallido.")
        return

    smtp_cfg = _get_smtp_cfg(db)

    # Plantilla: usa la de la BD o fallback genérico
    asunto_tpl = "Nómina – [mes] | [empresa]"
    cuerpo_tpl = (
        "Estimado/a [nombre],\n\n"
        "Adjuntamos tu documento de nómina correspondiente al período [mes].\n\n"
        "Atentamente,\nDpto. RRHH – [empresa]"
    )
    if envio.plantilla:
        asunto_tpl = envio.plantilla.asunto
        cuerpo_tpl = envio.plantilla.cuerpo_html

    # Conectar SMTP
    try:
        conn = smtplib.SMTP(smtp_cfg["host"], smtp_cfg["port"])
        if smtp_cfg["use_tls"]:
            conn.ehlo()
            conn.starttls()
            conn.ehlo()
            conn.login(smtp_cfg["user"], smtp_cfg["password"])
        print(f"[SMTP] Conexión establecida → {smtp_cfg['host']}:{smtp_cfg['port']}")
    except Exception as e:
        envio.estado = EnvioEstado.fallido
        db.commit()
        print(f"[SMTP ERROR] No se pudo conectar: {e}")
        print("[SMTP] Para modo local, inicia: python -m smtpd -c DebuggingServer -n localhost:1025")
        return

    empleados  = envio.grupo.empleados
    grupo_id   = envio.grupo_id
    enviados_ok    = 0
    enviados_fallo = 0

    print(f"\n[EMAIL] Inicio de envío masivo | Envío #{envio_id} | {len(empleados)} destinatarios")
    print("=" * 60)

    with conn:
        for emp in empleados:
            nombre_completo = f"{emp.nombre} {emp.apellido}"
            email = (emp.email or "").strip()

            # Validación de correo
            if not EMAIL_REGEX.match(email):
                log = LogEnvio(
                    envio_id=envio_id, empleado_id=emp.id,
                    estado=LogEstado.fallo, error_message="Email inválido o vacío"
                )
                db.add(log)
                enviados_fallo += 1
                print(f"  [{emp.cedula}] {nombre_completo:<25}  SKIP — email inválido: '{email}'")
                continue

            ruta_pdf = _buscar_pdf(emp.cedula, envio_id, grupo_id)

            try:
                msg = _construir_correo(
                    nombre_completo, email,
                    asunto_tpl, cuerpo_tpl,
                    smtp_cfg["remitente"], ruta_pdf
                )
                conn.sendmail(smtp_cfg["remitente"], email, msg.as_string())
                log = LogEnvio(
                    envio_id=envio_id, empleado_id=emp.id,
                    pdf_filename=ruta_pdf.name if ruta_pdf else None,
                    estado=LogEstado.ok
                )
                db.add(log)
                enviados_ok += 1
                pdf_tag = f"+ PDF:{ruta_pdf.name}" if ruta_pdf else "(sin PDF)"
                print(f"  [{emp.cedula}] {nombre_completo:<25}  OK → {email}  {pdf_tag}")

            except smtplib.SMTPRecipientsRefused:
                log = LogEnvio(envio_id=envio_id, empleado_id=emp.id,
                               estado=LogEstado.fallo, error_message="Destinatario rechazado por SMTP")
                db.add(log)
                enviados_fallo += 1
                print(f"  [{emp.cedula}] {nombre_completo:<25}  ERROR — destinatario rechazado")
            except Exception as e:
                log = LogEnvio(envio_id=envio_id, empleado_id=emp.id,
                               estado=LogEstado.fallo, error_message=str(e))
                db.add(log)
                enviados_fallo += 1
                print(f"  [{emp.cedula}] {nombre_completo:<25}  ERROR — {e}")

    envio.total         = len(empleados)
    envio.enviados_ok   = enviados_ok
    envio.enviados_fallo = enviados_fallo
    envio.estado        = EnvioEstado.completado
    envio.ejecutado_en  = datetime.utcnow()
    db.commit()

    print("=" * 60)
    print(f"[EMAIL] Envío #{envio_id} finalizado | OK: {enviados_ok} | Fallos: {enviados_fallo} | Total: {len(empleados)}\n")


# ---------------------------------------------------------------------------
# Resumen post-envío para el supervisor (audit trail)
# ---------------------------------------------------------------------------

def send_resumen_supervisor(envio_id: int, db: Session) -> None:
    """
    Notifica al supervisor con un resumen del envío ejecutado.
    Implementado como print de auditoría para la demo.
    En producción: enviar correo real vía SMTP al supervisor responsable.
    """
    envio = db.query(Envio).filter(Envio.id == envio_id).first()
    if not envio:
        return
    try:
        db.refresh(envio)
        operador  = envio.creador.nombre if envio.creador else "Desconocido"
        grupo     = envio.grupo.nombre  if envio.grupo   else "Sin grupo"
        print("\n" + "=" * 50)
        print("RESUMEN DE AUDITORÍA — Notificación Supervisor")
        print(f"  Envío   : {envio.nombre}")
        print(f"  Operador: {operador}  |  Grupo: {grupo}")
        print(f"  Total   : {envio.total}  |  OK: {envio.enviados_ok}  |  Fallos: {envio.enviados_fallo}")
        print("=" * 50 + "\n")
    except Exception as e:
        print(f"[RESUMEN ERROR] {e}")
