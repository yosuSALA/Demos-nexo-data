"""
End-to-end integration tests — runs the full pipeline on a temp TSV file
and validates the state of the DuckDB output.

These tests are slower than unit tests and are tagged with @pytest.mark.integration
so they can be run separately:
    pytest -m integration
"""

import pytest
from pathlib import Path

from etl.extract import iter_csv_chunks
from etl.load import finalize, init_db, load_chunk
from etl.transform import transform_chunk
from tests.conftest import TSV_CONTENT, sample_tsv  # noqa: F401


pytestmark = pytest.mark.integration


def run_pipeline(tsv_path: Path, db_path: Path, chunk_size: int = 1_000) -> int:
    """Minimal pipeline run — mirrors run_pipeline.py main() logic."""
    conn = init_db(db_path)
    total = 0
    for chunk_num, raw_df in iter_csv_chunks(tsv_path, chunk_size):
        clean_df = transform_chunk(raw_df, chunk_num)
        if not clean_df.is_empty():
            total += load_chunk(conn, clean_df, chunk_num)
    finalize(conn, sql_dir=None)   # skip mart creation in tests
    return total


# ---------------------------------------------------------------------------
# Full pipeline tests
# ---------------------------------------------------------------------------

class TestFullPipeline:
    def test_pipeline_loads_expected_row_count(self, sample_tsv, tmp_path):
        n = run_pipeline(sample_tsv, tmp_path / "out.duckdb")
        assert n == 6

    def test_pipeline_is_idempotent(self, sample_tsv, tmp_path):
        """Running the pipeline twice must not duplicate rows in the DB."""
        db_path = tmp_path / "out.duckdb"
        run_pipeline(sample_tsv, db_path)
        run_pipeline(sample_tsv, db_path)

        conn = init_db(db_path)
        total = conn.execute("SELECT COUNT(*) FROM financial_statements").fetchone()[0]
        conn.close()
        assert total == 6

    def test_pipeline_with_chunk_size_1(self, sample_tsv, tmp_path):
        """chunk_size=1 forces 6 separate chunks — must still load all 6 rows."""
        n = run_pipeline(sample_tsv, tmp_path / "out.duckdb", chunk_size=1)
        assert n == 6

    def test_all_account_codes_present(self, sample_tsv, tmp_path):
        db_path = tmp_path / "out.duckdb"
        run_pipeline(sample_tsv, db_path)
        conn = init_db(db_path)
        codes = {
            row[0] for row in conn.execute(
                "SELECT account_code FROM financial_statements"
            ).fetchall()
        }
        conn.close()
        assert codes == {"1", "101", "10101", "502.03.08", "101.02.02.02.08", "98"}

    def test_values_are_parsed_correctly(self, sample_tsv, tmp_path):
        db_path = tmp_path / "out.duckdb"
        run_pipeline(sample_tsv, db_path)
        conn = init_db(db_path)
        values = {
            row[0]: row[1] for row in conn.execute(
                "SELECT account_code, value FROM financial_statements"
            ).fetchall()
        }
        conn.close()
        assert values["1"]     == pytest.approx(1_188_854.66)
        assert values["101"]   == pytest.approx(900_000.00)
        assert values["10101"] == pytest.approx(340_818.85)

    def test_dates_normalized_to_iso(self, sample_tsv, tmp_path):
        db_path = tmp_path / "out.duckdb"
        run_pipeline(sample_tsv, db_path)
        conn = init_db(db_path)
        dates = {
            row[0] for row in conn.execute(
                "SELECT DISTINCT date FROM financial_statements"
            ).fetchall()
        }
        conn.close()
        assert dates == {"2023-12-31", "2023-03-31", "2025-02-28", "2023-11-30"}

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            run_pipeline(tmp_path / "missing.tsv", tmp_path / "out.duckdb")


# ---------------------------------------------------------------------------
# Multi-company TSV
# ---------------------------------------------------------------------------

MULTI_COMPANY_TSV = "\n".join([
    # Company A — ANUAL
    "\t".join(["22","SECTOR A","1111111111111","Company A","31/12/2023","ANUAL","1","ACTIVO","500.000,00",""]),
    "\t".join(["22","SECTOR A","1111111111111","Company A","31/12/2023","ANUAL","2","PASIVO","200.000,00",""]),
    # Company B — ANUAL
    "\t".join(["33","SECTOR B","2222222222222","Company B","31/12/2023","ANUAL","1","ACTIVO","800.000,00",""]),
    "\t".join(["33","SECTOR B","2222222222222","Company B","31/12/2023","ANUAL","2","PASIVO","300.000,00",""]),
    # Company A — prior year (different date → not a duplicate)
    "\t".join(["22","SECTOR A","1111111111111","Company A","31/12/2022","ANUAL","1","ACTIVO","420.000,00",""]),
])


class TestMultiCompanyPipeline:
    @pytest.fixture
    def multi_tsv(self, tmp_path) -> Path:
        path = tmp_path / "multi.tsv"
        path.write_text(MULTI_COMPANY_TSV, encoding="utf-8")
        return path

    def test_all_rows_loaded(self, multi_tsv, tmp_path):
        n = run_pipeline(multi_tsv, tmp_path / "out.duckdb")
        assert n == 5

    def test_two_companies_present(self, multi_tsv, tmp_path):
        db_path = tmp_path / "out.duckdb"
        run_pipeline(multi_tsv, db_path)
        conn = init_db(db_path)
        rucs = {
            row[0] for row in conn.execute(
                "SELECT DISTINCT ruc FROM financial_statements"
            ).fetchall()
        }
        conn.close()
        assert rucs == {"1111111111111", "2222222222222"}

    def test_two_years_for_company_a(self, multi_tsv, tmp_path):
        db_path = tmp_path / "out.duckdb"
        run_pipeline(multi_tsv, db_path)
        conn = init_db(db_path)
        years = conn.execute(
            "SELECT COUNT(DISTINCT date) FROM financial_statements "
            "WHERE ruc = '1111111111111'"
        ).fetchone()[0]
        conn.close()
        assert years == 2

    def test_assets_greater_than_liabilities_for_all_companies(self, multi_tsv, tmp_path):
        db_path = tmp_path / "out.duckdb"
        run_pipeline(multi_tsv, db_path)
        conn = init_db(db_path)
        violations = conn.execute("""
            SELECT COUNT(*) FROM (
                SELECT
                    ruc,
                    SUM(CASE WHEN account_code = '1' THEN value END) AS assets,
                    SUM(CASE WHEN account_code = '2' THEN value END) AS liabilities
                FROM financial_statements
                GROUP BY ruc, date
                HAVING liabilities > assets
            )
        """).fetchone()[0]
        conn.close()
        assert violations == 0
