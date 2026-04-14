"""main.py — orquestador bot SRI.

Uso:
    python main.py --anio 2026 --mes 3
    python main.py --anio 2026 --mes 3 --debug   # browser visible
"""
from __future__ import annotations
import argparse
import logging
import sys
from datetime import datetime

import config
from src.scraper import SRIScraper
from src.processor import DataProcessor
from src.exporter import ExcelExporter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("main")


def parse_args():
    now = datetime.now()
    p = argparse.ArgumentParser(description="Bot SRI: descarga + cruce facturas/retenciones")
    p.add_argument("--anio", type=int, default=now.year)
    p.add_argument("--mes", type=int, default=now.month)
    p.add_argument("--debug", action="store_true", help="browser visible (no headless)")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    headless = config.HEADLESS and not args.debug

    if not config.RUC or not config.CLAVE:
        log.error("falta SRI_RUC / SRI_CLAVE en .env")
        return 1

    try:
        with SRIScraper(
            ruc=config.RUC,
            clave=config.CLAVE,
            download_dir=config.DOWNLOAD_DIR,
            headless=headless,
            timeout_ms=config.TIMEOUT_MS,
        ) as bot:
            bot.login()
            fact_path = bot.descargar_facturas(args.anio, args.mes)
            ret_path = bot.descargar_retenciones(args.anio, args.mes)

        proc = DataProcessor(fact_path, ret_path)
        proc.cargar()
        df = proc.cruzar()

        out = config.OUTPUT_DIR / f"cruce_SRI_{args.anio}_{args.mes:02d}.xlsx"
        ExcelExporter(out).exportar(df)

        log.info(f"✔ listo → {out}")
        return 0

    except Exception as e:
        log.exception(f"fallo pipeline: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
