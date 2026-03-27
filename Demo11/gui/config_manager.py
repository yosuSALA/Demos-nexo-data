"""
config_manager.py — Persistencia de configuración de la aplicación
===================================================================
Guarda y restaura las preferencias del usuario (rutas de archivos,
configuración de programación, filtros) en un archivo JSON local.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def _get_app_root() -> Path:
    """
    Retorna la raíz de la aplicación.
    - En desarrollo: el directorio del proyecto (padre de gui/).
    - Compilado con PyInstaller --onefile: el directorio donde vive el .exe,
      NO el directorio temporal sys._MEIPASS (donde se descomprimen los assets).
      La configuración del usuario debe vivir junto al .exe para ser persistente.
    """
    if getattr(sys, "frozen", False):
        # sys.executable apunta al .exe → su parent es la carpeta del .exe
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


APP_ROOT = _get_app_root()

# Archivo de configuración junto al ejecutable (persistente)
CONFIG_PATH = APP_ROOT / "config" / "etl_gui_config.json"


def get_bundled_path(relative: str) -> Path:
    """
    Resuelve una ruta a un recurso empaquetado (sql/, config/ de solo lectura).
    En desarrollo usa la raíz del proyecto; compilado usa sys._MEIPASS.
    """
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / relative
    return Path(__file__).resolve().parent.parent / relative

# Valores por defecto de la aplicación
DEFAULTS: dict[str, Any] = {
    # Ruta de la base de datos destino
    "ruta_db": "output/sib_final.duckdb",

    # Modo de ejecución: "update" (actualizar) o "create" (crear nueva)
    "modo": "update",

    # Programación automática
    "programacion_dia": 5,        # Día del mes
    "programacion_hora": "09:00",
    "programacion_activa": False,

    # Apariencia
    "tema": "dark",
}


def load_config() -> dict[str, Any]:
    """Carga la configuración desde disco. Si no existe, retorna los valores por defecto."""
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                saved = json.load(f)
            # Mezcla con defaults para cubrir claves nuevas añadidas en futuras versiones
            merged = {**DEFAULTS, **saved}
            return merged
        except (json.JSONDecodeError, OSError):
            pass
    return dict(DEFAULTS)


def save_config(config: dict[str, Any]) -> None:
    """Persiste la configuración a disco en formato JSON legible."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
