"""
Data quality tests — business rule validation on loaded financial statements.

These tests verify domain-level invariants after data is written to DuckDB:
  - RUC format (Ecuador 13-digit tax ID)
  - Account code structure and hierarchy
  - Valid date range
  - Period type values
  - Value finite range (no inf / NaN)
  - Account hierarchy consistency (child <= parent)
  - No orphan account classifications
"""

import math
import pytest
import polars as pl

from etl.load import load_chunk
from etl.transform import transform_chunk
from tests.conftest import make_raw_df, make_valid_df, mem_db  # noqa: F401

VALID_PERIOD_TYPES = {"ANUAL", "MENSUAL", "TRIMESTRAL", "SEMESTRAL"}
VALID_ACCOUNT_CLASSES = {"1", "2", "3", "4", "5"}
MIN_YEAR = 2000
MAX_YEAR = 2030


def seed_db(conn, rows: list[dict]) -> None:
    """Transform and load a list of raw row dicts into the DB."""
    df = transform_chunk(make_raw_df(rows), chunk_num=1)
    if not df.is_empty():
        load_chunk(conn, df, chunk_num=1)


def fetch_all(conn, sql: str) -> list[tuple]:
    return conn.execute(sql).fetchall()


# ---------------------------------------------------------------------------
# RUC format
# ---------------------------------------------------------------------------

class TestRucFormat:
    def test_valid_ruc_is_accepted(self, mem_db):
        seed_db(mem_db, [make_valid_df().to_dicts()[0]])
        count = mem_db.execute(
            "SELECT COUNT(*) FROM financial_statements WHERE LENGTH(ruc) = 13"
        ).fetchone()[0]
        assert count == 1

    @pytest.mark.parametrize("bad_ruc", [
        "123",             # too short
        "12345678901234",  # too long
        "ABC4567890123",   # non-numeric characters
        "",                # empty — dropped by transform
    ])
    def test_ruc_not_13_digits_is_rejected(self, mem_db, bad_ruc):
        """RUC must be exactly 13 numeric characters."""
        row = make_valid_df().to_dicts()[0]
        row["ruc"] = bad_ruc
        seed_db(mem_db, [row])
        invalid = mem_db.execute(
            "SELECT COUNT(*) FROM financial_statements "
            "WHERE LENGTH(ruc) != 13 OR ruc SIMILAR TO '%[^0-9]%'"
        ).fetchone()[0]
        assert invalid == 0, f"Row with RUC '{bad_ruc}' should not be in the DB"

    def test_no_null_ruc_in_db(self, mem_db):
        seed_db(mem_db, [make_valid_df().to_dicts()[0]])
        nulls = mem_db.execute(
            "SELECT COUNT(*) FROM financial_statements WHERE ruc IS NULL OR ruc = ''"
        ).fetchone()[0]
        assert nulls == 0


# ---------------------------------------------------------------------------
# Account code structure
# ---------------------------------------------------------------------------

class TestAccountCodeStructure:
    def test_valid_class_level_code_stored(self, mem_db):
        seed_db(mem_db, [make_valid_df(account_code="1").to_dicts()[0]])
        row = mem_db.execute(
            "SELECT account_code FROM financial_statements LIMIT 1"
        ).fetchone()
        assert row[0] == "1"

    @pytest.mark.parametrize("code", ["1", "101", "10101", "2", "201", "20101"])
    def test_valid_account_codes_accepted(self, mem_db, code):
        seed_db(mem_db, [make_valid_df(account_code=code).to_dicts()[0]])
        found = mem_db.execute(
            "SELECT COUNT(*) FROM financial_statements WHERE account_code = ?", [code]
        ).fetchone()[0]
        assert found == 1

    def test_account_code_first_digit_is_valid_class(self, mem_db):
        """After loading, every account_code must start with 1–5."""
        for code in ["1", "2", "3", "4", "5"]:
            row = make_valid_df(account_code=code, ruc=f"000000000000{code}").to_dicts()[0]
            seed_db(mem_db, [row])
        invalid = mem_db.execute(
            "SELECT COUNT(*) FROM financial_statements "
            "WHERE LEFT(account_code, 1) NOT IN ('1','2','3','4','5')"
        ).fetchone()[0]
        assert invalid == 0

    def test_no_null_account_code_in_db(self, mem_db):
        seed_db(mem_db, [make_valid_df().to_dicts()[0]])
        nulls = mem_db.execute(
            "SELECT COUNT(*) FROM financial_statements "
            "WHERE account_code IS NULL OR account_code = ''"
        ).fetchone()[0]
        assert nulls == 0


# ---------------------------------------------------------------------------
# Date validity
# ---------------------------------------------------------------------------

class TestDateValidity:
    def test_date_stored_in_iso_format(self, mem_db):
        seed_db(mem_db, [make_valid_df(date="31/12/2023").to_dicts()[0]])
        date_val = mem_db.execute(
            "SELECT date FROM financial_statements LIMIT 1"
        ).fetchone()[0]
        # Must match YYYY-MM-DD
        assert len(date_val) == 10
        assert date_val[4] == "-" and date_val[7] == "-"

    def test_fiscal_year_is_within_valid_range(self, mem_db):
        seed_db(mem_db, [make_valid_df(date="31/12/2023").to_dicts()[0]])
        out_of_range = mem_db.execute(
            f"SELECT COUNT(*) FROM financial_statements "
            f"WHERE date IS NOT NULL "
            f"AND (YEAR(CAST(date AS DATE)) < {MIN_YEAR} "
            f"  OR YEAR(CAST(date AS DATE)) > {MAX_YEAR})"
        ).fetchone()[0]
        assert out_of_range == 0

    @pytest.mark.parametrize("date_str, expected_iso", [
        ("01/01/2014", "2014-01-01"),
        ("31/12/2023", "2023-12-31"),
    ])
    def test_date_conversion_roundtrip(self, mem_db, date_str, expected_iso):
        seed_db(mem_db, [make_valid_df(date=date_str, account_code="101").to_dicts()[0]])
        result = mem_db.execute(
            "SELECT date FROM financial_statements WHERE account_code = '101'"
        ).fetchone()[0]
        assert result == expected_iso


# ---------------------------------------------------------------------------
# Period type
# ---------------------------------------------------------------------------

class TestPeriodType:
    @pytest.mark.parametrize("period", ["ANUAL", "MENSUAL", "TRIMESTRAL", "SEMESTRAL"])
    def test_valid_period_types_accepted(self, mem_db, period):
        seed_db(mem_db, [make_valid_df(period_type=period, account_code="2").to_dicts()[0]])
        found = mem_db.execute(
            "SELECT COUNT(*) FROM financial_statements WHERE period_type = ?", [period]
        ).fetchone()[0]
        assert found == 1

    def test_no_unexpected_period_types_in_db(self, mem_db):
        for period in ["ANUAL", "MENSUAL"]:
            row = make_valid_df(period_type=period,
                                ruc=f"000000000{period[:4]}").to_dicts()[0]
            seed_db(mem_db, [row])
        unexpected = mem_db.execute(
            "SELECT COUNT(*) FROM financial_statements "
            "WHERE period_type NOT IN ('ANUAL','MENSUAL','TRIMESTRAL','SEMESTRAL')"
        ).fetchone()[0]
        assert unexpected == 0


# ---------------------------------------------------------------------------
# Value integrity
# ---------------------------------------------------------------------------

class TestValueIntegrity:
    def test_no_null_values_in_db(self, mem_db):
        seed_db(mem_db, [make_valid_df().to_dicts()[0]])
        nulls = mem_db.execute(
            "SELECT COUNT(*) FROM financial_statements WHERE value IS NULL"
        ).fetchone()[0]
        assert nulls == 0

    def test_value_is_finite(self, mem_db):
        """Python float inf must never reach the DB."""
        seed_db(mem_db, [make_valid_df(value="1.000,00").to_dicts()[0]])
        val = mem_db.execute(
            "SELECT value FROM financial_statements LIMIT 1"
        ).fetchone()[0]
        assert math.isfinite(val)

    def test_negative_values_are_stored(self, mem_db):
        """Negative values are valid (e.g. corrections, write-downs)."""
        seed_db(mem_db, [make_valid_df(value="-500,00").to_dicts()[0]])
        val = mem_db.execute(
            "SELECT value FROM financial_statements LIMIT 1"
        ).fetchone()[0]
        assert val == pytest.approx(-500.0)

    def test_zero_value_is_stored(self, mem_db):
        seed_db(mem_db, [make_valid_df(value="0,00").to_dicts()[0]])
        val = mem_db.execute(
            "SELECT value FROM financial_statements LIMIT 1"
        ).fetchone()[0]
        assert val == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Account hierarchy consistency
# ---------------------------------------------------------------------------

class TestAccountHierarchy:
    def _seed_hierarchy(self, mem_db, class_val, group_val, subgroup_val):
        rows = [
            make_valid_df(account_code="1",     value=class_val,    ruc="1000000000001").to_dicts()[0],
            make_valid_df(account_code="101",   value=group_val,    ruc="1000000000001").to_dicts()[0],
            make_valid_df(account_code="10101", value=subgroup_val, ruc="1000000000001").to_dicts()[0],
        ]
        seed_db(mem_db, rows)

    def test_class_value_is_loaded(self, mem_db):
        self._seed_hierarchy(mem_db, "1.188.854,66", "900.000,00", "340.818,85")
        row = mem_db.execute(
            "SELECT value FROM financial_statements WHERE account_code = '1'"
        ).fetchone()
        assert row[0] == pytest.approx(1_188_854.66)

    def test_all_hierarchy_levels_present(self, mem_db):
        self._seed_hierarchy(mem_db, "1.188.854,66", "900.000,00", "340.818,85")
        codes = {
            row[0] for row in mem_db.execute(
                "SELECT account_code FROM financial_statements"
            ).fetchall()
        }
        assert {"1", "101", "10101"}.issubset(codes)

    def test_parent_value_gte_largest_child(self, mem_db):
        """
        The class-level account (1 digit) should be >= any 3-digit child.
        This is a structural invariant of the Supercias chart of accounts.
        """
        self._seed_hierarchy(mem_db, "1.188.854,66", "900.000,00", "340.818,85")
        violation = mem_db.execute("""
            SELECT COUNT(*) FROM (
                SELECT
                    parent.value AS parent_val,
                    child.value  AS child_val
                FROM financial_statements parent
                JOIN financial_statements child
                  ON LEFT(child.account_code, 1) = parent.account_code
                 AND LENGTH(child.account_code)  = 3
                 AND child.ruc         = parent.ruc
                 AND child.date        = parent.date
                 AND child.period_type = parent.period_type
                WHERE child.value > parent.value
            )
        """).fetchone()[0]
        assert violation == 0


# ---------------------------------------------------------------------------
# Deduplication uniqueness in DB
# ---------------------------------------------------------------------------

class TestDatabaseUniqueness:
    def test_unique_key_constraint_prevents_duplicate_rows(self, mem_db):
        df = transform_chunk(make_valid_df(n=1), chunk_num=1)
        load_chunk(mem_db, df, chunk_num=1)
        load_chunk(mem_db, df, chunk_num=2)  # second insert must be ignored
        assert mem_db.execute(
            "SELECT COUNT(*) FROM financial_statements"
        ).fetchone()[0] == 1

    def test_same_company_different_years_both_stored(self, mem_db):
        row_2022 = make_valid_df(date="31/12/2022").to_dicts()[0]
        row_2023 = make_valid_df(date="31/12/2023").to_dicts()[0]
        seed_db(mem_db, [row_2022, row_2023])
        assert mem_db.execute(
            "SELECT COUNT(*) FROM financial_statements"
        ).fetchone()[0] == 2
