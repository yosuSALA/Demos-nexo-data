"""
main.py — Demo #13: Orquestador del pipeline completo
Ejecuta en secuencia: Scraping → Comparación → Alertas

Uso:
    python main.py                        # pipeline completo (scraping real)
    python main.py --sin-scraping         # saltea el scraping, usa CSV existente
    python main.py --paginas 5            # raspa N páginas (default: 3)
    python main.py --umbral 5             # alerta a partir del 5% de diferencia
    python main.py --volumen 100          # 100 unidades/mes por SKU
"""
import asyncio
import argparse
import logging
import sys
import pandas as pd

from scraper    import scrape_competitor
from comparador import cargar_datos_empresa, cargar_datos_competidor, calcular_diferencias
from alertas    import detectar_alertas, formatear_alerta_email, UMBRAL_ALERTA_PCT, VOLUMEN_MENSUAL

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s",
)
logger = logging.getLogger(__name__)

SEPARADOR = "─" * 72


def banner(texto: str) -> None:
    print(f"\n{SEPARADOR}")
    print(f"  {texto}")
    print(SEPARADOR)


# ─── Paso 1: Scraping ───────────────────────────────────────────────────────

async def paso_scraping(max_pages: int) -> pd.DataFrame:
    banner(f"PASO 1/3 — Extracción de precios del competidor ({max_pages} páginas)")
    df = await scrape_competitor(max_pages=max_pages)
    if df.empty:
        logger.error("El scraper no retornó datos. Abortando pipeline.")
        sys.exit(1)
    print(f"\n  ✓ {len(df)} productos extraídos → precios_competidor_A.csv")
    return df


# ─── Paso 2: Comparación ────────────────────────────────────────────────────

def paso_comparacion(df_competidor: pd.DataFrame) -> pd.DataFrame:
    banner("PASO 2/3 — Cruce y cálculo de diferencias de precio")
    df_empresa     = cargar_datos_empresa()
    df_comparacion = calcular_diferencias(df_empresa, df_competidor)

    if df_comparacion.empty:
        logger.error(
            "No se encontraron productos en común entre la empresa y el competidor.\n"
            "  → Verifica que los nombres en MI_EMPRESA_PRECIOS (comparador.py) "
            "coincidan con los scrapeados."
        )
        sys.exit(1)

    pd.set_option("display.max_colwidth", 55)
    pd.set_option("display.width", 160)
    print(f"\n  Productos en común: {len(df_comparacion)}")
    print(f"  Somos más caros:    {(df_comparacion['diff_porcentual'] > 0).sum()}")
    print(f"  Somos más baratos:  {(df_comparacion['diff_porcentual'] < 0).sum()}")

    df_comparacion.to_csv("comparacion_precios.csv", index=False, encoding="utf-8")
    print(f"\n  ✓ Guardado → comparacion_precios.csv")
    return df_comparacion


# ─── Paso 3: Alertas ────────────────────────────────────────────────────────

def paso_alertas(
    df_comparacion: pd.DataFrame,
    umbral_pct:      float,
    volumen_mensual: int,
) -> None:
    banner(f"PASO 3/3 — Detección de alertas (umbral: {umbral_pct:.0f}%)")
    df_alertas = detectar_alertas(df_comparacion, umbral_pct=umbral_pct)
    mensaje    = formatear_alerta_email(df_alertas, volumen_mensual=volumen_mensual, umbral_pct=umbral_pct)

    print(mensaje)

    if not df_alertas.empty:
        df_alertas.to_csv("alertas_precios.csv", index=False, encoding="utf-8")
        print(f"  ✓ Alertas exportadas → alertas_precios.csv")


# ─── Pipeline principal ─────────────────────────────────────────────────────

async def pipeline(args: argparse.Namespace) -> None:
    print("\n" + "═" * 72)
    print("  DEMO #13 — SCRAPER DE PRECIOS DE COMPETENCIA")
    print("  books.toscrape.com  →  Comparación  →  Alertas automáticas")
    print("═" * 72)

    # 1. Scraping (o carga desde CSV existente)
    if args.sin_scraping:
        banner("PASO 1/3 — Cargando CSV existente (--sin-scraping activo)")
        df_competidor = cargar_datos_competidor()
    else:
        df_competidor = await paso_scraping(args.paginas)

    # 2. Comparación
    df_comparacion = paso_comparacion(df_competidor)

    # 3. Alertas
    paso_alertas(df_comparacion, umbral_pct=args.umbral, volumen_mensual=args.volumen)

    print(f"\n{'═'*72}")
    print("  Pipeline completado.")
    print(f"{'═'*72}\n")


# ─── CLI ────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Demo #13 — Scraper de precios de competencia",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--sin-scraping", action="store_true",
        help="Omite el scraping y usa el CSV existente (precios_competidor_A.csv)",
    )
    parser.add_argument(
        "--paginas", type=int, default=3, metavar="N",
        help="Número de páginas a scrapear",
    )
    parser.add_argument(
        "--umbral", type=float, default=UMBRAL_ALERTA_PCT, metavar="PCT",
        help="Umbral de diferencia porcentual para generar alerta",
    )
    parser.add_argument(
        "--volumen", type=int, default=VOLUMEN_MENSUAL, metavar="UNIDADES",
        help="Volumen mensual de ventas por SKU (para estimación de impacto)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(pipeline(args))
