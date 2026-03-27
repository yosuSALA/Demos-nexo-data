import polars as pl
from loguru import logger

from utils.formatters import normalize_date, parse_ec_number

# ---------------------------------------------------------------------------
# Configuración de columnas — coincide con COLUMN_NAMES en extract.py
# ---------------------------------------------------------------------------
NUMERIC_COLUMNS = ["value"]          # Números formato EC → Float64
DATE_COLUMNS    = ["date"]           # dd/mm/yyyy → cadena ISO 8601

# Un registro financiero único se identifica por empresa + cuenta + fecha + periodo.
DEDUP_SUBSET = ["ruc", "account_code", "date", "period_type"]

# Las filas a las que les falte cualquiera de estos campos son inválidas y se eliminan.
CRITICAL_COLUMNS = ["ruc", "account_code", "value"]

# ---------------------------------------------------------------------------
# Notas sobre formatos observados en los datos reales SIB
# ---------------------------------------------------------------------------
# sector_code : puede traer puntos de miles (ej. "15.036" → limpiar a "15036")
# account_code: dos formatos coexisten en el mismo dataset:
#   - Entero simple : 1, 101, 10101       (datos ANUALES, plan de cuentas consolidado)
#   - Jerarquía con puntos: 502.03.08, 101.02.02.02.08  (datos MENSUALES, NIIF detallado)
#   - El primer dígito siempre indica la clase (1=Activo, 2=Pasivo, 3=Patrimonio,
#     4=Ingresos, 5=Gastos, 6-9=Especiales/Fuera de balance)
# entity_subtype: vacío en ANUAL; contiene "FIDEICOMISO MERCANTIL" u otro subtipo en MENSUAL


def _clean_numeric_expr(col: str) -> pl.Expr:
    """
    Expresión vectorizada que convierte cadenas de números formato EC a Float64.

    Pasos (dentro del motor de Polars — sin bucles Python por fila):
      1. Elimina espacios en blanco
      2. Quita puntos de miles (1.188.854 → 1188854)
      3. Reemplaza coma decimal por punto (1188854,66 → 1188854.66)
      4. Convierte a Float64
    """
    return (
        pl.col(col)
        .str.strip_chars()
        .str.replace_all(".", "", literal=True)        # eliminar todos los puntos (miles)
        .str.replace(",", ".", literal=True)           # decimal coma -> punto
        .cast(pl.Float64, strict=False)                 # inválido -> null
        .alias(col)
    )


def _clean_date_expr(col: str) -> pl.Expr:
    """
    Intenta formatos de fecha comunes en orden y devuelve cadena ISO 8601.
    strptime de Polars con strict=False devuelve null si no coincide el formato,
    por lo que encadenamos coalesce para probar cada uno.
    """
    formats = ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%Y%m%d", "%d/%m/%y"]

    attempts = [
        pl.col(col).str.strip_chars().str.strptime(pl.Date, fmt, strict=False)
        for fmt in formats
    ]
    # coalesce devuelve el primer resultado que no sea nulo
    return pl.coalesce(attempts).cast(pl.Utf8).alias(col)


def transform_chunk(df: pl.DataFrame, chunk_num: int) -> pl.DataFrame:
    """
    Aplica todos los pasos de limpieza a un solo bloque:
      - parseo numérico
      - normalización de fechas
      - deduplicación dentro del bloque
      - eliminar filas donde campos críticos sean nulos
    """
    original_rows = len(df)

    # 1. Columnas numéricas (formato Ecuador → Float64)
    numeric_exprs = [_clean_numeric_expr(c) for c in NUMERIC_COLUMNS if c in df.columns]

    # 2. Columnas de fecha
    date_exprs = [_clean_date_expr(c) for c in DATE_COLUMNS if c in df.columns]

    # 3. Columnas de texto: quitar espacios en todo lo demás
    str_cols = [
        c for c in df.columns
        if c not in NUMERIC_COLUMNS and c not in DATE_COLUMNS
    ]
    str_exprs = [pl.col(c).str.strip_chars() for c in str_cols]

    df = df.with_columns(numeric_exprs + date_exprs + str_exprs)

    # 4a. Limpiar sector_code: quitar puntos de miles (ej. "15.036" → "15036")
    #     En datos ANUALES viene sin punto ("22"); en MENSUAL puede traer punto ("15.036").
    if "sector_code" in df.columns:
        df = df.with_columns(
            pl.col("sector_code").str.replace_all(r"\.", "").alias("sector_code")
        )

    # 4b. Eliminar filas con nulos o strings vacíos en columnas críticas
    critical = [c for c in CRITICAL_COLUMNS if c in df.columns]
    df = df.drop_nulls(subset=critical)
    str_critical = [c for c in critical if df.schema.get(c) == pl.Utf8]
    if str_critical:
        df = df.filter(
            pl.all_horizontal([pl.col(c).str.len_chars() > 0 for c in str_critical])
        )

    # 4b2. Validar formato RUC: exactamente 13 dígitos numéricos
    if "ruc" in df.columns:
        df = df.filter(pl.col("ruc").str.contains(r"^\d{13}$"))

    # 4c. Deduplicación intra-bloque (mantiene la primera ocurrencia)
    dedup_cols = [c for c in DEDUP_SUBSET if c in df.columns]
    if dedup_cols:
        df = df.unique(subset=dedup_cols, keep="first", maintain_order=False)

    dropped = original_rows - len(df)
    if dropped:
        logger.debug(f"Bloque {chunk_num}: descartadas {dropped:,} filas (nulos/duplicados)")

    return df
