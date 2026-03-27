"""
Fixtures compartidos para la suite de tests del ETL Supercias.
"""

from pathlib import Path

import duckdb
import polars as pl
import pytest

from etl.load import CREATE_TABLE_SQL, CREATE_DEDUP_INDEX_SQL


# ---------------------------------------------------------------------------
# Fila base válida — refleja los 10 campos reales del TSV
# ---------------------------------------------------------------------------
# Notas sobre los formatos observados en datos reales:
#   sector_code   : puede traer puntos de miles ("15.036") → se limpia en transform
#   account_code  : dos formatos: entero ("1","101") o jerarquía con puntos ("502.03.08")
#   entity_subtype: vacío en ANUAL; "FIDEICOMISO MERCANTIL" u otro en MENSUAL

VALID_ROW_ANUAL = {
    "sector_code":    "22",
    "entity_type":    "ADMINISTRADORA DE FONDOS Y FIDEICOMISOS",
    "ruc":            "0991290915001",
    "company_name":   "FUTURFID S.A.",
    "date":           "31/12/2023",
    "period_type":    "ANUAL",
    "account_code":   "1",
    "account_name":   "ACTIVO",
    "value":          "1.188.854,66",
    "entity_subtype": "",                 # vacío en datos ANUAL
}

VALID_ROW_MENSUAL = {
    "sector_code":    "15.036",           # con punto de miles — se limpia a "15036"
    "entity_type":    "ADMINISTRADORA DE FONDOS Y FIDEICOMISOS",
    "ruc":            "1792754658001",
    "company_name":   "FIDUTLAN S.A.",
    "date":           "31/03/2023",
    "period_type":    "MENSUAL",
    "account_code":   "502.03.08",        # formato con puntos (datos MENSUAL)
    "account_name":   "VALUACION DE INSTRUMENTOS FINANCIEROS",
    "value":          "9.450,00",
    "entity_subtype": "",
}

VALID_ROW_FIDEICOMISO = {
    "sector_code":    "2.118",            # con punto de miles → "2118"
    "entity_type":    "NEGOCIO FIDUCIARIO INSCRITO",
    "ruc":            "0992722657001",
    "company_name":   "FIDEICOMISO MERCANTIL INMOBILIARIO OPORTO",
    "date":           "28/02/2025",
    "period_type":    "MENSUAL",
    "account_code":   "101.02.02.02.08",  # jerarquía profunda
    "account_name":   "CERTIFICADOS DE DEPÓSITO",
    "value":          "600.000,00",
    "entity_subtype": "FIDEICOMISO MERCANTIL",  # columna 10 con contenido
}

VALID_ROW_NEGATIVO = {
    "sector_code":    "30.018",
    "entity_type":    "NEGOCIO FIDUCIARIO INSCRITO",
    "ruc":            "1792628415001",
    "company_name":   "FIDEICOMISO MERCANTIL INMOBILIARIO LOTE M",
    "date":           "30/11/2023",
    "period_type":    "MENSUAL",
    "account_code":   "98",               # código especial (fuera del rango 1–5)
    "account_name":   "CAMBIOS EN ACTIVOS Y PASIVOS:",
    "value":          "-190.089,41",      # valor negativo
    "entity_subtype": "FIDEICOMISO MERCANTIL",
}

# Alias por compatibilidad con tests existentes
VALID_ROW = VALID_ROW_ANUAL


def make_raw_df(rows: list[dict]) -> pl.DataFrame:
    """DataFrame Polars con todos los campos como Utf8 — igual que la lectura del CSV."""
    keys = list(rows[0].keys())
    return pl.DataFrame(rows, schema={k: pl.Utf8 for k in keys})


def make_valid_df(overrides: dict | None = None, n: int = 1, **kwargs) -> pl.DataFrame:
    """Devuelve n filas únicas de VALID_ROW_ANUAL con campos opcionales sobreescritos.

    Acepta overrides como dict posicional o como keyword arguments:
        make_valid_df({"account_code": "101"})
        make_valid_df(account_code="101")

    Cuando n > 1, genera filas únicas variando account_code (si no se especificó)
    o ruc (si account_code fue sobreescrito) para evitar deduplicación.
    """
    merged = {**(overrides or {}), **kwargs}
    base = {**VALID_ROW_ANUAL, **merged}
    if n == 1:
        rows = [base]
    elif "account_code" not in merged:
        rows = [{**base, "account_code": str(i)} for i in range(1, n + 1)]
    else:
        rows = [{**base, "ruc": f"{i:013d}"} for i in range(1, n + 1)]
    return make_raw_df(rows)


def make_mensual_df(overrides: dict | None = None) -> pl.DataFrame:
    """Devuelve una fila MENSUAL con account_code en formato de puntos."""
    row = {**VALID_ROW_MENSUAL, **(overrides or {})}
    return make_raw_df([row])


# ---------------------------------------------------------------------------
# Fixtures de DuckDB
# ---------------------------------------------------------------------------

@pytest.fixture
def mem_db() -> duckdb.DuckDBPyConnection:
    """DuckDB en memoria con la tabla financial_statements e índice único."""
    conn = duckdb.connect(":memory:")
    conn.execute(CREATE_TABLE_SQL)
    try:
        conn.execute(CREATE_DEDUP_INDEX_SQL)
    except duckdb.CatalogException:
        pass
    yield conn
    conn.close()


@pytest.fixture
def file_db(tmp_path: Path) -> duckdb.DuckDBPyConnection:
    """DuckDB en archivo temporal (para tests de integración)."""
    conn = duckdb.connect(str(tmp_path / "test.duckdb"))
    conn.execute(CREATE_TABLE_SQL)
    try:
        conn.execute(CREATE_DEDUP_INDEX_SQL)
    except duckdb.CatalogException:
        pass
    yield conn
    conn.close()


# ---------------------------------------------------------------------------
# Fixture de archivo TSV — combina filas ANUAL y MENSUAL
# ---------------------------------------------------------------------------

TSV_CONTENT = "\n".join([
    # Fila ANUAL — cuenta raíz entera, sector_code sin punto, entity_subtype vacío
    "\t".join(["22", "ADMINISTRADORA DE FONDOS Y FIDEICOMISOS",
               "0991290915001", "FUTURFID S.A.",
               "31/12/2023", "ANUAL", "1", "ACTIVO", "1.188.854,66", ""]),
    "\t".join(["22", "ADMINISTRADORA DE FONDOS Y FIDEICOMISOS",
               "0991290915001", "FUTURFID S.A.",
               "31/12/2023", "ANUAL", "101", "ACTIVO CORRIENTE", "900.000,00", ""]),
    "\t".join(["22", "ADMINISTRADORA DE FONDOS Y FIDEICOMISOS",
               "0991290915001", "FUTURFID S.A.",
               "31/12/2023", "ANUAL", "10101", "EFECTIVO Y EQUIVALENTES", "340.818,85", ""]),
    # Fila MENSUAL — account_code con puntos, sector_code con punto de miles
    "\t".join(["15.036", "ADMINISTRADORA DE FONDOS Y FIDEICOMISOS",
               "1792754658001", "FIDUTLAN S.A.",
               "31/03/2023", "MENSUAL", "502.03.08",
               "VALUACION DE INSTRUMENTOS FINANCIEROS", "9.450,00", ""]),
    # Fila MENSUAL — jerarquía profunda, entity_subtype con contenido
    "\t".join(["2.118", "NEGOCIO FIDUCIARIO INSCRITO",
               "0992722657001", "FIDEICOMISO MERCANTIL INMOBILIARIO OPORTO",
               "28/02/2025", "MENSUAL", "101.02.02.02.08",
               "CERTIFICADOS DE DEPÓSITO", "600.000,00", "FIDEICOMISO MERCANTIL"]),
    # Fila MENSUAL — valor negativo, código especial 98
    "\t".join(["30.018", "NEGOCIO FIDUCIARIO INSCRITO",
               "1792628415001", "FIDEICOMISO MERCANTIL INMOBILIARIO LOTE M",
               "30/11/2023", "MENSUAL", "98",
               "CAMBIOS EN ACTIVOS Y PASIVOS:", "-190.089,41", "FIDEICOMISO MERCANTIL"]),
])


@pytest.fixture
def sample_tsv(tmp_path: Path) -> Path:
    """Escribe el archivo TSV de muestra en un directorio temporal y retorna su ruta."""
    path = tmp_path / "sample.tsv"
    path.write_text(TSV_CONTENT, encoding="utf-8")
    return path
