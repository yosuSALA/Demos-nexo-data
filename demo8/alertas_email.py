"""
Motor de Alertas por Email
Soporta modo dry_run (log) y live (SMTP real).
"""

import os
import smtplib
import logging
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pandas as pd

from config import (
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD,
    EMAIL_MODE, ALERT_LOG, LOG_DIR,
)

# ── Logging ───────────────────────────────────────────────────
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    filename=ALERT_LOG,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    encoding="utf-8",
)
logger = logging.getLogger(__name__)

# ── Plantilla HTML del email ──────────────────────────────────
PLANTILLA_HTML = """\
<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8">
<style>
  body {{ font-family: Arial, sans-serif; color: #333; margin: 0; padding: 0; }}
  .header {{ background: {color_header}; padding: 20px 30px; }}
  .header h2 {{ color: #fff; margin: 0; font-size: 18px; }}
  .body {{ padding: 24px 30px; }}
  .badge {{ display:inline-block; background:{color_header}; color:#fff;
            padding:4px 12px; border-radius:4px; font-weight:bold; }}
  table {{ width:100%; border-collapse:collapse; margin-top:16px; }}
  td {{ padding: 8px 12px; border-bottom: 1px solid #eee; }}
  td:first-child {{ color:#666; width:40%; }}
  .footer {{ background:#f5f5f5; padding:12px 30px; font-size:12px; color:#999; }}
</style>
</head>
<body>
  <div class="header">
    <h2>&#9888; Alerta de Vencimiento — {umbral} dias restantes</h2>
  </div>
  <div class="body">
    <p>Estimado/a <strong>{responsable}</strong>,</p>
    <p>La siguiente obligacion requiere su atencion inmediata:</p>
    <table>
      <tr><td>ID Obligacion</td><td><strong>{id_obligacion}</strong></td></tr>
      <tr><td>Tipo</td><td>{tipo}</td></tr>
      <tr><td>Entidad</td><td>{entidad}</td></tr>
      <tr><td>Fecha de Vencimiento</td><td><strong>{fecha_vencimiento}</strong></td></tr>
      <tr><td>Dias Restantes</td><td><span class="badge">{umbral} dias</span></td></tr>
      <tr><td>Valor en Riesgo</td><td><strong>USD {valor}</strong></td></tr>
    </table>
    <p style="margin-top:20px;">Por favor, gestione la renovacion o cierre antes del vencimiento.</p>
  </div>
  <div class="footer">
    Mensaje automatico generado por el Sistema Monitor de Contratos y Obligaciones.<br>
    Enviado el {fecha_envio}
  </div>
</body>
</html>
"""

COLORES_UMBRAL = {7: "#c0392b", 15: "#e67e22", 30: "#2980b9"}


def _construir_mensaje(row: pd.Series) -> MIMEMultipart:
    dias   = int(row["dias_para_vencer"])
    color  = COLORES_UMBRAL.get(dias, "#555")
    asunto = f"[ALERTA {dias}d] Vence '{row['tipo']}' — {row['entidad_relacionada']}"

    html = PLANTILLA_HTML.format(
        responsable      = row["responsable_interno"],
        umbral           = dias,
        id_obligacion    = row["id_obligacion"],
        tipo             = row["tipo"],
        entidad          = row["entidad_relacionada"],
        fecha_vencimiento= str(row["fecha_vencimiento"])[:10],
        valor            = f"{row['valor_usd']:,.2f}",
        fecha_envio      = datetime.now().strftime("%d/%m/%Y %H:%M"),
        color_header     = color,
    )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = asunto
    msg["From"]    = SMTP_USER or "monitor@demo.com"
    msg["To"]      = f"{row['responsable_interno']} <{SMTP_USER or 'demo@demo.com'}>"
    msg.attach(MIMEText(html, "html", "utf-8"))
    return msg


def _enviar_smtp(msg: MIMEMultipart) -> bool:
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(msg["From"], msg["To"], msg.as_string())
        return True
    except Exception as exc:
        logger.error("SMTP error: %s", exc)
        return False


def _dry_run(msg: MIMEMultipart, row: pd.Series) -> None:
    logger.info(
        "DRY-RUN | Para: %s | Asunto: %s | ID: %s | Dias: %s | USD: %.2f",
        row["responsable_interno"],
        msg["Subject"],
        row["id_obligacion"],
        int(row["dias_para_vencer"]),
        row["valor_usd"],
    )


# ── API pública ───────────────────────────────────────────────

UMBRALES = {7, 15, 30}


def procesar_alertas(df: pd.DataFrame) -> dict:
    """
    Filtra registros en umbrales 7/15/30 dias y ejecuta envio
    segun EMAIL_MODE. Retorna resumen de resultados.
    """
    criticos = df[df["dias_para_vencer"].isin(UMBRALES)].copy()
    resultado = {"total": len(criticos), "enviados": 0, "fallidos": 0, "modo": EMAIL_MODE}

    if criticos.empty:
        logger.info("Sin obligaciones en umbrales criticos hoy.")
        return resultado

    for _, row in criticos.iterrows():
        msg = _construir_mensaje(row)

        if EMAIL_MODE == "live":
            ok = _enviar_smtp(msg)
            if ok:
                resultado["enviados"] += 1
                logger.info("ENVIADO | %s | %s", row["id_obligacion"], msg["Subject"])
            else:
                resultado["fallidos"] += 1
        else:
            _dry_run(msg, row)
            resultado["enviados"] += 1

    print(f"[Alertas] Modo={EMAIL_MODE} | Total={resultado['total']} "
          f"| Enviados={resultado['enviados']} | Fallidos={resultado['fallidos']}")
    return resultado


if __name__ == "__main__":
    from etl_contratos import generar_datos, transformar
    df = transformar(generar_datos())
    procesar_alertas(df)
