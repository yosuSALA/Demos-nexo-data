"""
main_gui.py — Punto de entrada del Motor Analítico ETL Super Cías
==================================================================
Uso interactivo:
    python main_gui.py

Uso automático (invocado por Windows Task Scheduler):
    python main_gui.py --auto

En modo --auto, ejecuta el ETL con descarga directa desde Super Cías
sin mostrar la ventana y registra el resultado en etl_gui.log.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))


def _run_auto() -> None:
    """Ejecución automática sin GUI (para Task Scheduler)."""
    from loguru import logger

    from gui.backend import run_etl
    from gui.config_manager import load_config

    logger.add(PROJECT_ROOT / "etl_gui.log", rotation="5 MB", encoding="utf-8")
    logger.info("Ejecución automática iniciada (Task Scheduler)")

    cfg = load_config()
    db_path = Path(cfg.get("ruta_db", "output/sib_final.duckdb"))
    mode = cfg.get("modo", "update")

    def log_progress(msg: str, pct: float) -> None:
        logger.info(f"[{pct:.0%}] {msg}")

    resultado = run_etl(duckdb_path=db_path, mode=mode, on_progress=log_progress)

    if resultado.exitoso:
        logger.info(
            f"ETL automático completado — {resultado.filas_cargadas:,} filas cargadas "
            f"en {resultado.duracion_seg:.1f}s"
        )
    else:
        logger.error(f"ETL automático falló: {resultado.mensaje_error}")
        sys.exit(1)


def _run_gui() -> None:
    """Lanza la aplicación gráfica interactiva."""
    from gui.app import ETLApp

    app = ETLApp()
    app.mainloop()


if __name__ == "__main__":
    if "--auto" in sys.argv:
        _run_auto()
    else:
        _run_gui()
