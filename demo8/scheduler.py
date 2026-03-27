"""
Scheduler Diario — APScheduler
Ejecuta el ETL + motor de alertas una vez al dia a la hora configurada.
Correr con: python scheduler.py
"""

import sys
import logging
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from config import SCHEDULER_HOUR, SCHEDULER_MINUTE, CSV_PATH, LOG_DIR, ALERT_LOG
from etl_contratos import generar_datos, transformar, guardar_csv
from alertas_email import procesar_alertas

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(
    filename=ALERT_LOG,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    encoding="utf-8",
)
logger = logging.getLogger(__name__)

scheduler = BlockingScheduler(timezone="America/Santiago")


def job_diario():
    inicio = datetime.now()
    print(f"\n[Scheduler] Job iniciado: {inicio.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=== JOB DIARIO INICIADO ===")

    try:
        df_raw = generar_datos(n=100)
        df     = transformar(df_raw)
        guardar_csv(df, CSV_PATH)
        resultado = procesar_alertas(df)

        logger.info(
            "Job completado | Rojo=%d | Amarillo=%d | Verde=%d | Alertas=%d",
            (df["estado_semaforo"] == "Rojo").sum(),
            (df["estado_semaforo"] == "Amarillo").sum(),
            (df["estado_semaforo"] == "Verde").sum(),
            resultado["total"],
        )
        print(f"[Scheduler] Job completado en {(datetime.now()-inicio).seconds}s")

    except Exception as exc:
        logger.error("Error en job_diario: %s", exc, exc_info=True)
        print(f"[Scheduler] ERROR: {exc}")


def main():
    print("=" * 55)
    print("  Scheduler — Monitor de Contratos y Obligaciones")
    print(f"  Hora programada: {SCHEDULER_HOUR:02d}:{SCHEDULER_MINUTE:02d} diario")
    print("  Ctrl+C para detener")
    print("=" * 55)

    # Ejecutar inmediatamente al arrancar
    print("\n[Scheduler] Ejecutando job inicial...")
    job_diario()

    # Programar ejecucion diaria
    trigger = CronTrigger(hour=SCHEDULER_HOUR, minute=SCHEDULER_MINUTE)
    scheduler.add_job(job_diario, trigger, id="job_diario", name="ETL + Alertas")

    print(f"\n[Scheduler] Proximo run: {SCHEDULER_HOUR:02d}:{SCHEDULER_MINUTE:02d}")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("\n[Scheduler] Detenido por el usuario.")


if __name__ == "__main__":
    main()
