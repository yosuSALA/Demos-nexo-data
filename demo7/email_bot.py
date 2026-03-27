"""
email_bot.py  —  Demo #7: Bot de envío masivo de reportes por email
====================================================================
Flujo:
  1. Lee clientes_reportes.csv con pandas
  2. Para cada cliente, construye un correo personalizado (MIMEMultipart)
  3. Adjunta el PDF correspondiente desde /reportes_mensuales
  4. Envía vía SMTP y registra resultados en envios.log

Modos SMTP disponibles (ver sección CONFIGURACIÓN más abajo):
  - LOCAL (default): servidor de debug  →  python -m smtpd -c DebuggingServer -n localhost:1025
  - GMAIL            : Gmail con Contraseña de Aplicación (TLS, puerto 587)
"""

import smtplib
import logging
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from datetime import datetime

import pandas as pd

# ---------------------------------------------------------------------------
# CONFIGURACIÓN
# ---------------------------------------------------------------------------

# --- Modo LOCAL (servidor de debug, sin autenticación) ---
SMTP_HOST     = "localhost"
SMTP_PORT     = 1025
SMTP_USER     = None          # No se usa en modo local
SMTP_PASSWORD = None          # No se usa en modo local
USE_TLS       = False
REMITENTE     = "bot-reportes@fiduciaria-demo.com"

# --- Modo GMAIL (descomenta este bloque y comenta el de arriba) ---
# Para obtener la Contraseña de Aplicación:
#   Google Account → Seguridad → Verificación en 2 pasos → Contraseñas de aplicaciones
# SMTP_HOST     = "smtp.gmail.com"
# SMTP_PORT     = 587
# SMTP_USER     = "tu_cuenta@gmail.com"
# SMTP_PASSWORD = "xxxx xxxx xxxx xxxx"   # Contraseña de Aplicación (16 chars)
# USE_TLS       = True
# REMITENTE     = "tu_cuenta@gmail.com"

CSV_PATH      = "clientes_reportes.csv"
REPORTES_DIR  = Path("reportes_mensuales")
LOG_FILE      = "envios.log"

# ---------------------------------------------------------------------------
# LOGGING  — escribe en consola Y en envios.log al mismo tiempo
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# VALIDACIÓN DE CORREO
# ---------------------------------------------------------------------------
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def es_email_valido(correo: str) -> bool:
    return bool(EMAIL_REGEX.match(correo.strip()))

# ---------------------------------------------------------------------------
# CONSTRUCCIÓN DEL CORREO
# ---------------------------------------------------------------------------
ASUNTO_TEMPLATE = "Tu estado de cuenta – {nombre} | Marzo 2026"

CUERPO_TEMPLATE = """\
Estimado/a {nombre},

Nos complace enviarte tu estado de cuenta correspondiente al mes de Marzo 2026.

Encontrarás adjunto el documento con el detalle de tus inversiones y movimientos
registrados durante el período.

Si tienes alguna consulta, no dudes en contactarnos respondiendo este correo o
llamando a nuestra línea de atención al cliente.

Atentamente,
Área de Reportes
Fiduciaria Demo S.A.
"""

def construir_correo(nombre: str, correo_destino: str, ruta_pdf: Path) -> MIMEMultipart:
    """Arma el objeto MIMEMultipart con asunto, cuerpo y PDF adjunto."""
    msg = MIMEMultipart()
    msg["From"]    = REMITENTE
    msg["To"]      = correo_destino.strip()
    msg["Subject"] = ASUNTO_TEMPLATE.format(nombre=nombre)

    # Cuerpo en texto plano
    msg.attach(MIMEText(CUERPO_TEMPLATE.format(nombre=nombre), "plain", "utf-8"))

    # Adjunto PDF
    with open(ruta_pdf, "rb") as f:
        parte = MIMEBase("application", "octet-stream")
        parte.set_payload(f.read())
    encoders.encode_base64(parte)
    parte.add_header(
        "Content-Disposition",
        f'attachment; filename="{ruta_pdf.name}"',
    )
    msg.attach(parte)

    return msg

# ---------------------------------------------------------------------------
# ENVÍO SMTP
# ---------------------------------------------------------------------------
def abrir_conexion_smtp() -> smtplib.SMTP:
    """Crea y devuelve una conexión SMTP lista para usar."""
    conn = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
    if USE_TLS:
        conn.ehlo()
        conn.starttls()
        conn.ehlo()
        conn.login(SMTP_USER, SMTP_PASSWORD)
    return conn

# ---------------------------------------------------------------------------
# PIPELINE PRINCIPAL
# ---------------------------------------------------------------------------
def procesar_envios():
    # 1. Leer CSV
    try:
        df = pd.read_csv(CSV_PATH, encoding="utf-8")
    except FileNotFoundError:
        log.error("No se encontró '%s'. Ejecuta primero setup_mock_data.py", CSV_PATH)
        return

    columnas_requeridas = {"id_cliente", "nombre", "correo", "nombre_archivo_pdf"}
    if not columnas_requeridas.issubset(df.columns):
        log.error("El CSV no tiene las columnas esperadas: %s", columnas_requeridas)
        return

    total    = len(df)
    enviados = 0
    errores  = 0

    log.info("=" * 60)
    log.info("INICIO DE ENVÍO MASIVO  |  %d destinatarios  |  %s", total, datetime.now().strftime("%Y-%m-%d %H:%M"))
    log.info("=" * 60)

    # 2. Abrir conexión SMTP una sola vez (eficiente para envíos masivos)
    try:
        smtp = abrir_conexion_smtp()
        log.info("Conexión SMTP establecida → %s:%s", SMTP_HOST, SMTP_PORT)
    except Exception as e:
        log.critical("No se pudo conectar al servidor SMTP: %s", e)
        log.critical("Asegúrate de que el servidor esté corriendo:")
        log.critical("  python -m smtpd -c DebuggingServer -n localhost:1025")
        return

    # 3. Iterar sobre cada cliente
    with smtp:
        for _, fila in df.iterrows():
            id_c    = fila["id_cliente"]
            nombre  = str(fila["nombre"]).strip()
            correo  = str(fila["correo"]).strip()
            archivo = str(fila["nombre_archivo_pdf"]).strip()

            # -- Validación 1: formato de correo --
            if not es_email_valido(correo):
                log.warning("[%s] %-20s  SKIP — correo inválido: '%s'", id_c, nombre, correo)
                errores += 1
                continue

            # -- Validación 2: PDF existe --
            ruta_pdf = REPORTES_DIR / archivo
            if not ruta_pdf.exists():
                log.warning("[%s] %-20s  SKIP — PDF no encontrado: '%s'", id_c, nombre, ruta_pdf)
                errores += 1
                continue

            # -- Construir y enviar --
            try:
                msg = construir_correo(nombre, correo, ruta_pdf)
                smtp.sendmail(REMITENTE, correo, msg.as_string())
                log.info("[%s] %-20s  OK   → %s", id_c, nombre, correo)
                enviados += 1

            except smtplib.SMTPRecipientsRefused:
                log.warning("[%s] %-20s  ERROR — destinatario rechazado: %s", id_c, nombre, correo)
                errores += 1
            except smtplib.SMTPException as e:
                log.error("[%s] %-20s  ERROR SMTP — %s", id_c, nombre, e)
                errores += 1
            except Exception as e:
                log.error("[%s] %-20s  ERROR inesperado — %s", id_c, nombre, e)
                errores += 1

    # 4. Resumen final
    log.info("=" * 60)
    log.info("RESUMEN: %d enviados | %d errores | %d total", enviados, errores, total)
    log.info("Log completo guardado en: %s", LOG_FILE)
    log.info("=" * 60)


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    procesar_envios()
