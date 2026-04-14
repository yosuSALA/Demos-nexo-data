"""
comparador.py — Demo #13: Lógica de Comparación de Precios
Cruza los precios propios con los del competidor y calcula diferencias.
"""
import logging
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s — %(levelname)s — %(message)s")
logger = logging.getLogger(__name__)

COMPETITOR_FILE = "precios_competidor_A.csv"

# ─── Precios propios (simulados) ────────────────────────────────────────────
# Los nombres deben coincidir exactamente con los extraídos de books.toscrape.com.
# Los precios están en USD para simular el escenario de retail.
# Estrategia de precios diseñada para el demo:
#   · Algunos están por encima del competidor  → disparan alerta
#   · Algunos están por debajo                 → ventaja competitiva
#   · Algunos están casi iguales               → zona neutral

MI_EMPRESA_PRECIOS = [
    # nombre (debe coincidir con el scrapeado)                                              precio_empresa
    {"nombre": "A Light in the Attic",                                                      "precio_empresa": 56.50},  # +9.1% → ALERTA
    {"nombre": "Tipping the Velvet",                                                        "precio_empresa": 54.00},  # ~+0.5% → ok
    {"nombre": "Soumission",                                                                "precio_empresa": 52.00},  # ~+3.8% → ALERTA
    {"nombre": "Sharp Objects",                                                             "precio_empresa": 45.00},  # por debajo → ganando
    {"nombre": "Sapiens: A Brief History of Humankind",                                     "precio_empresa": 58.00},  # +7% → ALERTA
    {"nombre": "The Requiem Red",                                                           "precio_empresa": 21.00},  # por debajo → ganando
    {"nombre": "The Dirty Little Secrets of Getting Your Dream Job",                        "precio_empresa": 35.00},  # +5% → ALERTA
    {"nombre": "The Boys in the Boat: Nine Americans and Their Quest for Gold at the 1936 Berlin Olympics",
                                                                                            "precio_empresa": 22.00},  # casi igual → ok
    {"nombre": "The Black Maria",                                                           "precio_empresa": 54.00},  # +3.5% → ALERTA
    {"nombre": "Starving Hearts (Triangular Trade Trilogy, #1)",                            "precio_empresa": 14.50},  # +3.6% → ALERTA
    {"nombre": "Shakespeare's Sonnets",                                                     "precio_empresa": 21.00},  # ~+1.6% → ok
    {"nombre": "Set Me Free",                                                               "precio_empresa": 17.00},  # por debajo → ganando
    {"nombre": "Scott Pilgrim's Precious Little Life (Scott Pilgrim #1)",                   "precio_empresa": 57.00},  # +9% → ALERTA
    {"nombre": "Rip it Up and Start Again",                                                 "precio_empresa": 35.50},  # ~+1.4% → ok
    {"nombre": "Our Band Could Be Your Life: Scenes from the American Indie Underground, 1981-1991",
                                                                                            "precio_empresa": 59.00},  # ~+4% → ALERTA
]


# ─── Carga de datos ──────────────────────────────────────────────────────────

def cargar_datos_empresa() -> pd.DataFrame:
    """Retorna el DataFrame con los precios propios."""
    df = pd.DataFrame(MI_EMPRESA_PRECIOS)
    logger.info(f"Precios propios cargados: {len(df)} SKUs")
    return df


def cargar_datos_competidor(filepath: str = COMPETITOR_FILE) -> pd.DataFrame:
    """Carga el CSV generado por scraper.py."""
    try:
        df = pd.read_csv(filepath, encoding="utf-8")
        logger.info(f"Precios del competidor cargados: {len(df)} productos desde '{filepath}'")
        return df
    except FileNotFoundError:
        logger.error(
            f"Archivo '{filepath}' no encontrado. "
            "Ejecuta primero: python scraper.py"
        )
        raise


# ─── Lógica de comparación ───────────────────────────────────────────────────

def calcular_diferencias(
    df_empresa:     pd.DataFrame,
    df_competidor:  pd.DataFrame,
) -> pd.DataFrame:
    """
    Cruza ambos DataFrames por 'nombre' y calcula:
      - diff_absoluta:   precio_empresa − precio_competidor
      - diff_porcentual: (precio_empresa − precio_competidor) / precio_empresa × 100

    Un valor positivo indica que somos más caros que el competidor (riesgo de pérdida de ventas).
    Un valor negativo indica que somos más baratos (ventaja competitiva).
    """
    df = pd.merge(
        df_empresa,
        df_competidor[["nombre", "precio_competidor", "disponibilidad"]],
        on="nombre",
        how="inner",
    )

    if df.empty:
        logger.warning(
            "El merge no produjo resultados. "
            "Verifica que los nombres en MI_EMPRESA_PRECIOS coincidan con los scrapeados."
        )
        return df

    df["diff_absoluta"]   = (df["precio_empresa"] - df["precio_competidor"]).round(2)
    df["diff_porcentual"] = (
        (df["precio_empresa"] - df["precio_competidor"]) / df["precio_empresa"] * 100
    ).round(2)

    # Ordena de mayor a menor diferencia (los más urgentes al tope)
    df = df.sort_values("diff_porcentual", ascending=False).reset_index(drop=True)

    logger.info(
        f"Comparación completada: {len(df)} productos en común | "
        f"Más caros: {(df['diff_porcentual'] > 0).sum()} | "
        f"Más baratos: {(df['diff_porcentual'] < 0).sum()}"
    )
    return df


# ─── Ejecución directa ───────────────────────────────────────────────────────

if __name__ == "__main__":
    df_empresa     = cargar_datos_empresa()
    df_competidor  = cargar_datos_competidor()
    df_comparacion = calcular_diferencias(df_empresa, df_competidor)

    print(f"\n{'─'*90}")
    print("TABLA DE COMPARACIÓN DE PRECIOS")
    print(f"{'─'*90}")
    pd.set_option("display.max_colwidth", 55)
    pd.set_option("display.width", 150)
    print(df_comparacion.to_string(index=False))

    df_comparacion.to_csv("comparacion_precios.csv", index=False, encoding="utf-8")
    print(f"\n✓ Guardado → 'comparacion_precios.csv'")
