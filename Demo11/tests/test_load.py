"""
Tests for etl/load.py — DuckDB schema, deduplication index, and chunk loading.
"""

import polars as pl
import pytest

from etl.load import init_db, load_chunk
from etl.transform import transform_chunk
from tests.conftest import make_valid_df, mem_db  # noqa: F401


def loaded_count(conn) -> int:
    return conn.execute("SELECT COUNT(*) FROM financial_statements").fetchone()[0]


def clean(df: pl.DataFrame) -> pl.DataFrame:
    return transform_chunk(df, chunk_num=1)


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------

class TestSchema:
    def test_table_exists(self, mem_db):
        result = mem_db.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_name = 'financial_statements'"
        ).fetchone()
        assert result is not None

    def test_required_columns_exist(self, mem_db):
        cols = {
            row[0] for row in mem_db.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'financial_statements'"
            ).fetchall()
        }
        required = {"ruc", "account_code", "value", "date", "period_type",
                    "sector_code", "entity_type", "company_name", "account_name"}
        assert required.issubset(cols)

    def test_unique_index_exists(self, mem_db):
        indexes = mem_db.execute(
            "SELECT index_name FROM duckdb_indexes() "
            "WHERE table_name = 'financial_statements'"
        ).fetchall()
        index_names = {row[0] for row in indexes}
        assert "uix_stmt" in index_names

    def test_init_db_is_idempotent(self, tmp_path):
        """Calling init_db twice on the same file must not raise."""
        db_path = tmp_path / "idempotent.duckdb"
        conn = init_db(db_path)
        conn.close()
        conn2 = init_db(db_path)
        conn2.close()


# ---------------------------------------------------------------------------
# load_chunk behaviour
# ---------------------------------------------------------------------------

class TestLoadChunk:
    def test_inserts_valid_rows(self, mem_db):
        df = clean(make_valid_df(n=3))
        load_chunk(mem_db, df, chunk_num=1)
        assert loaded_count(mem_db) == 3

    def test_returns_correct_row_count(self, mem_db):
        df = clean(make_valid_df(n=5))
        result = load_chunk(mem_db, df, chunk_num=1)
        assert result == 5

    def test_cross_chunk_duplicates_are_ignored(self, mem_db):
        """Loading the same chunk twice must not create duplicate rows."""
        df = clean(make_valid_df(n=1))
        load_chunk(mem_db, df, chunk_num=1)
        load_chunk(mem_db, df, chunk_num=2)
        assert loaded_count(mem_db) == 1

    def test_values_stored_correctly(self, mem_db):
        df = clean(make_valid_df(value="1.188.854,66"))
        load_chunk(mem_db, df, chunk_num=1)
        row = mem_db.execute(
            "SELECT ruc, account_code, value FROM financial_statements LIMIT 1"
        ).fetchone()
        assert row[0] == "0991290915001"
        assert row[1] == "1"
        assert row[2] == pytest.approx(1_188_854.66)

    def test_date_stored_as_iso_string(self, mem_db):
        df = clean(make_valid_df(date="31/12/2023"))
        load_chunk(mem_db, df, chunk_num=1)
        date_val = mem_db.execute(
            "SELECT date FROM financial_statements LIMIT 1"
        ).fetchone()[0]
        assert date_val == "2023-12-31"

    def test_multiple_companies_all_inserted(self, mem_db):
        df1 = clean(make_valid_df(ruc="0000000000001"))
        df2 = clean(make_valid_df(ruc="0000000000002"))
        df3 = clean(make_valid_df(ruc="0000000000003"))
        for i, df in enumerate([df1, df2, df3], start=1):
            load_chunk(mem_db, df, chunk_num=i)
        assert loaded_count(mem_db) == 3

    def test_empty_dataframe_does_not_raise(self, mem_db):
        """An empty chunk (all rows dropped in transform) must be a no-op."""
        empty = pl.DataFrame(schema={
            "sector_code": pl.Utf8, "entity_type": pl.Utf8, "ruc": pl.Utf8,
            "company_name": pl.Utf8, "date": pl.Utf8, "period_type": pl.Utf8,
            "account_code": pl.Utf8, "account_name": pl.Utf8, "value": pl.Float64,
        })
        load_chunk(mem_db, empty, chunk_num=1)
        assert loaded_count(mem_db) == 0
