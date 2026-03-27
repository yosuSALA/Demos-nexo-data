"""
Configuración centralizada — lee variables desde .env
"""

import os
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST       = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT       = int(os.getenv("SMTP_PORT", 587))
SMTP_USER       = os.getenv("SMTP_USER", "")
SMTP_PASSWORD   = os.getenv("SMTP_PASSWORD", "")
EMAIL_MODE      = os.getenv("EMAIL_MODE", "dry_run")   # "dry_run" | "live"
SCHEDULER_HOUR  = int(os.getenv("SCHEDULER_HOUR", 8))
SCHEDULER_MINUTE= int(os.getenv("SCHEDULER_MINUTE", 0))

CSV_PATH        = "datos_dashboard_contratos.csv"
LOG_DIR         = "logs"
ALERT_LOG       = f"{LOG_DIR}/alertas.log"
