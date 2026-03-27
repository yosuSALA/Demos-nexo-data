from pathlib import Path

import duckdb
import polars as pl
from loguru import logger

# ---------------------------------------------------------------------------
# El esquema coincide con las 10 columnas reales de la fuente TSV:
#   sector_code | entity_type | ruc | company_name | date | period_type
#   account_code | account_name | value | entity_subtype
#
# Cambios respecto a muestras ANUALES:
#   - sector_code puede traer puntos de miles (15.036) → se limpia en transform a "15036"
#   - account_code tiene DOS formatos: entero simple (101) o jerarquía (502.03.08)
#   - entity_subtype (col 10) antes siempre vacía, ahora contiene ej. "FIDEICOMISO MERCANTIL"
#   - account_code puede comenzar con 6–9 (cuentas especiales/fuera de balance)
# ---------------------------------------------------------------------------
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS financial_statements (
    sector_code    VARCHAR,           -- código de sector limpio (ej. 15036, 22)
    entity_type    VARCHAR,           -- etiqueta del sector
    ruc            VARCHAR NOT NULL,  -- RUC de 13 dígitos
    company_name   VARCHAR,           -- nombre legal completo
    date           VARCHAR,           -- fecha ISO 8601 (YYYY-MM-DD)
    period_type    VARCHAR,           -- ANUAL | MENSUAL | TRIMESTRAL | SEMESTRAL
    account_code   VARCHAR NOT NULL,  -- entero (1/101/10101) o puntos (502.03.08)
    account_name   VARCHAR,           -- nombre de la cuenta en español
    value          DOUBLE  NOT NULL,  -- valor numérico (puede ser negativo)
    entity_subtype VARCHAR,           -- subtipo: "FIDEICOMISO MERCANTIL" u otro, vacío si no aplica
    loaded_at      TIMESTAMP DEFAULT current_timestamp
);
"""

# Registro único = empresa + cuenta + fecha de reporte + granularidad de periodo
CREATE_DEDUP_INDEX_SQL = """
CREATE UNIQUE INDEX IF NOT EXISTS uix_stmt
    ON financial_statements (ruc, account_code, date, period_type);
"""


def init_db(db_path: str | Path) -> duckdb.DuckDBPyConnection:
    """Abre (o crea) el archivo DuckDB y asegura que el esquema exista."""
    conn = duckdb.connect(str(db_path))
    conn.execute(CREATE_TABLE_SQL)
    # DuckDB soporta índices únicos desde v0.10+ — se omite si la versión es anterior
    try:
        conn.execute(CREATE_DEDUP_INDEX_SQL)
    except duckdb.CatalogException:
        logger.warning("El índice único ya existe o no es soportado — omitiendo.")
    logger.info(f"DuckDB listo en '{db_path}'")
    return conn


def load_chunk(
    conn: duckdb.DuckDBPyConnection,
    df: pl.DataFrame,
    chunk_num: int,
) -> int:
    """
    Inserta un bloque de DataFrame de Polars en DuckDB usando un patrón
    INSERT OR IGNORE para omitir duplicados entre bloques.

    Los DataFrames de Polars se pasan a DuckDB como tablas Arrow — zero-copy,
    sin serialización intermedia a CSV.
    """
    # DuckDB puede consultar frames de Polars directamente vía el nombre de la variable local
    arrow_table = df.to_arrow()  # noqa: F841  (usado por DuckDB vía nombre)

    # Columnas presentes en el bloque que también existen en la tabla destino
    target_cols = [
        "sector_code", "entity_type", "ruc", "company_name",
        "date", "period_type", "account_code", "account_name", "value",
        "entity_subtype",
    ]
    available = [c for c in target_cols if c in df.columns]
    cols_sql = ", ".join(available)

    sql = f"""
        INSERT OR IGNORE INTO financial_statements ({cols_sql})
        SELECT {cols_sql}
        FROM arrow_table
    """
    conn.execute(sql)

    row_count = len(df)
    logger.debug(f"Bloque {chunk_num}: {row_count:,} filas escritas en DuckDB")
    return row_count


def build_marts(conn: duckdb.DuckDBPyConnection, sql_dir: str | Path) -> None:
    """
    Ejecuta todos los archivos SQL de 'marts' analíticos en orden (01_, 02_, …).
    Esto crea las vistas o tablas finales que consumirán las herramientas de BI.
    Se omiten archivos que no sigan el patrón numerado.
    """
    sql_dir = Path(sql_dir)
    # Busca archivos SQL que comiencen con números (ej. 01_mart_balance.sql)
    mart_files = sorted(f for f in sql_dir.glob("[0-9][1-9]_mart_*.sql"))
    if not mart_files:
        logger.warning(f"No se encontraron archivos SQL de marts en el directorio: '{sql_dir}'")
        return
    for path in mart_files:
        logger.info(f"Generando vista analítica (mart): {path.name}")
        conn.execute(path.read_text())
    logger.info(f"Proceso de marts finalizado ({len(mart_files)} vistas creadas)")


def finalize(conn: duckdb.DuckDBPyConnection, sql_dir: str | Path | None = None) -> None:
    """
    Finaliza el pipeline: construye marts analíticos opcionales, registra el conteo 
    final de registros cargados y cierra la conexión de forma segura.
    """
    if sql_dir is not None:
        build_marts(conn, sql_dir)
    
    # Obtiene el conteo total consolidado de la tabla principal
    total = conn.execute("SELECT COUNT(*) FROM financial_statements").fetchone()[0]
    logger.info(f"Carga completa — {total:,} registros totales en la tabla financial_statements")
    conn.close()
