"""
Tests para los formatos descubiertos en las nuevas muestras MENSUAL:
  - sector_code con puntos de miles  (15.036 → 15036)
  - account_code con jerarquía de puntos  (502.03.08, 101.02.02.02.08)
  - entity_subtype con contenido  ("FIDEICOMISO MERCANTIL")
  - valores negativos  (-190.089,41)
  - código de cuenta especial  (98 — fuera del rango 1–5)
"""

import pytest
import polars as pl

from etl.transform import transform_chunk
from etl.load import load_chunk
from etl.extract import COLUMN_NAMES, _assign_column_names
from tests.conftest import (
    make_raw_df,
    make_mensual_df,
    VALID_ROW_MENSUAL,
    VALID_ROW_FIDEICOMISO,
    VALID_ROW_NEGATIVO,
    mem_db,        # noqa: F401
    sample_tsv,    # noqa: F401
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def transform(row: dict) -> pl.DataFrame:
    return transform_chunk(make_raw_df([row]), chunk_num=1)


# ---------------------------------------------------------------------------
# sector_code con puntos de miles
# ---------------------------------------------------------------------------

class TestSectorCodeConPuntos:
    @pytest.mark.parametrize("raw, expected", [
        ("15.036", "15036"),
        ("2.118",  "2118"),
        ("30.018", "30018"),
        ("522",    "522"),    # sin punto — no debe cambiar
        ("22",     "22"),
    ])
    def test_limpia_punto_de_miles(self, raw, expected):
        df = transform({**VALID_ROW_MENSUAL, "sector_code": raw})
        assert df["sector_code"][0] == expected

    def test_sector_code_con_punto_no_afecta_otras_columnas(self):
        df = transform({**VALID_ROW_MENSUAL, "sector_code": "15.036"})
        assert len(df) == 1
        assert df["ruc"][0] == "1792754658001"


# ---------------------------------------------------------------------------
# account_code en formato jerárquico con puntos
# ---------------------------------------------------------------------------

class TestAccountCodeConPuntos:
    @pytest.mark.parametrize("code", [
        "502.03.08",
        "101.02.02.02.08",
        "98",
        "1",
        "101",
        "10101",
    ])
    def test_formato_variado_no_descarta_fila(self, code):
        df = transform({**VALID_ROW_MENSUAL, "account_code": code})
        assert len(df) == 1, f"Fila descartada con account_code='{code}'"

    def test_account_code_con_puntos_almacenado_tal_cual(self):
        df = transform(VALID_ROW_MENSUAL)
        assert df["account_code"][0] == "502.03.08"

    def test_jerarquia_profunda_almacenada_tal_cual(self):
        df = transform(VALID_ROW_FIDEICOMISO)
        assert df["account_code"][0] == "101.02.02.02.08"

    def test_codigo_especial_98_conservado(self):
        """El código 98 empieza con '9' (fuera del plan 1-5) — debe conservarse."""
        df = transform(VALID_ROW_NEGATIVO)
        assert len(df) == 1
        assert df["account_code"][0] == "98"

    def test_primer_digito_identifica_clase_en_ambos_formatos(self, mem_db):
        """LEFT(account_code, 1) debe funcionar igual para entero y formato con puntos."""
        for row in [VALID_ROW_MENSUAL, VALID_ROW_FIDEICOMISO]:
            df = transform_chunk(make_raw_df([row]), chunk_num=1)
            if not df.is_empty():
                load_chunk(mem_db, df, chunk_num=1)

        result = mem_db.execute("""
            SELECT account_code, LEFT(account_code, 1) AS clase
            FROM financial_statements
            WHERE account_code IN ('502.03.08', '101.02.02.02.08')
            ORDER BY account_code
        """).fetchall()

        codes = {row[0]: row[1] for row in result}
        assert codes.get("101.02.02.02.08") == "1"   # Activo
        assert codes.get("502.03.08") == "5"          # Gasto


# ---------------------------------------------------------------------------
# entity_subtype (columna 10 con contenido)
# ---------------------------------------------------------------------------

class TestEntitySubtype:
    def test_entity_subtype_con_contenido_es_preservado(self, mem_db):
        df = transform_chunk(make_raw_df([VALID_ROW_FIDEICOMISO]), chunk_num=1)
        assert not df.is_empty()
        load_chunk(mem_db, df, chunk_num=1)
        val = mem_db.execute(
            "SELECT entity_subtype FROM financial_statements "
            "WHERE ruc = '0992722657001' LIMIT 1"
        ).fetchone()[0]
        assert val == "FIDEICOMISO MERCANTIL"

    def test_entity_subtype_vacio_en_anual(self, mem_db):
        from tests.conftest import VALID_ROW_ANUAL
        df = transform_chunk(make_raw_df([VALID_ROW_ANUAL]), chunk_num=1)
        load_chunk(mem_db, df, chunk_num=1)
        val = mem_db.execute(
            "SELECT entity_subtype FROM financial_statements "
            "WHERE ruc = '0991290915001' LIMIT 1"
        ).fetchone()[0]
        assert val == "" or val is None

    def test_columna_entity_subtype_existe_en_schema(self, mem_db):
        cols = {
            row[0] for row in mem_db.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'financial_statements'"
            ).fetchall()
        }
        assert "entity_subtype" in cols


# ---------------------------------------------------------------------------
# Valores negativos
# ---------------------------------------------------------------------------

class TestValoresNegativos:
    def test_valor_negativo_es_parseado_correctamente(self):
        df = transform(VALID_ROW_NEGATIVO)
        assert len(df) == 1
        assert df["value"][0] == pytest.approx(-190_089.41)

    def test_valor_negativo_es_almacenado_en_db(self, mem_db):
        df = transform_chunk(make_raw_df([VALID_ROW_NEGATIVO]), chunk_num=1)
        load_chunk(mem_db, df, chunk_num=1)
        val = mem_db.execute(
            "SELECT value FROM financial_statements "
            "WHERE ruc = '1792628415001' LIMIT 1"
        ).fetchone()[0]
        assert val == pytest.approx(-190_089.41)

    def test_valor_negativo_tipo_float64(self):
        df = transform(VALID_ROW_NEGATIVO)
        assert df["value"].dtype == pl.Float64


# ---------------------------------------------------------------------------
# Lectura del TSV combinado (ANUAL + MENSUAL)
# ---------------------------------------------------------------------------

class TestTsvCombinado:
    def test_todas_las_filas_son_leidas(self, sample_tsv):
        from etl.extract import iter_csv_chunks
        total = sum(len(df) for _, df in iter_csv_chunks(sample_tsv, chunk_size=1_000))
        assert total == 6   # 3 ANUAL + 3 MENSUAL

    def test_columnas_son_los_10_campos(self, sample_tsv):
        from etl.extract import iter_csv_chunks
        _, df = next(iter_csv_chunks(sample_tsv, chunk_size=1_000))
        assert df.columns == COLUMN_NAMES
        assert "entity_subtype" in df.columns

    def test_sector_codes_limpios_tras_transform(self, sample_tsv):
        from etl.extract import iter_csv_chunks
        dfs = [
            transform_chunk(raw, i)
            for i, raw in iter_csv_chunks(sample_tsv, chunk_size=1_000)
        ]
        combined = pl.concat(dfs)
        # Ningún sector_code debe tener punto (ya fueron limpiados)
        con_punto = combined.filter(pl.col("sector_code").str.contains(r"\."))
        assert len(con_punto) == 0

    def test_period_types_presentes(self, sample_tsv):
        from etl.extract import iter_csv_chunks
        dfs = [
            transform_chunk(raw, i)
            for i, raw in iter_csv_chunks(sample_tsv, chunk_size=1_000)
        ]
        combined = pl.concat(dfs)
        periods = set(combined["period_type"].to_list())
        assert "ANUAL" in periods
        assert "MENSUAL" in periods

    def test_pipeline_completo_carga_tsv_mixto(self, sample_tsv, tmp_path):
        from etl.extract import iter_csv_chunks
        from etl.load import init_db, load_chunk, finalize

        db_path = tmp_path / "mixto.duckdb"
        conn = init_db(db_path)
        total = 0
        for i, raw in iter_csv_chunks(sample_tsv, chunk_size=1_000):
            clean = transform_chunk(raw, i)
            if not clean.is_empty():
                total += load_chunk(conn, clean, i)
        finalize(conn, sql_dir=None)

        conn2 = init_db(db_path)
        count = conn2.execute("SELECT COUNT(*) FROM financial_statements").fetchone()[0]
        conn2.close()

        # El código 98 (negativo) y todas las filas válidas deben estar cargadas
        assert count == total
        assert count >= 5   # mínimo: 3 ANUAL + 2 MENSUAL sin el negativo (98 es válido)
