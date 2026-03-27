"""
Tests for etl/transform.py — numeric cleaning, date normalization,
deduplication, null handling, and whitespace stripping.
"""

import pytest
import polars as pl

from etl.transform import transform_chunk
from tests.conftest import make_raw_df, make_valid_df


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def transform(rows: list[dict]) -> pl.DataFrame:
    return transform_chunk(make_raw_df(rows), chunk_num=1)


def transform_valid(**overrides) -> pl.DataFrame:
    return transform_chunk(make_valid_df(overrides), chunk_num=1)


# ---------------------------------------------------------------------------
# Numeric cleaning
# ---------------------------------------------------------------------------

class TestNumericCleaning:
    @pytest.mark.parametrize("raw, expected", [
        ("1.188.854,66",  1_188_854.66),
        ("1.000,00",      1_000.0),
        ("500,75",        500.75),
        ("0,00",          0.0),
        ("-2.500,30",     -2_500.30),
        ("340818,85",     340_818.85),
    ])
    def test_valid_ec_numbers(self, raw, expected):
        df = transform_valid(value=raw)
        assert df["value"][0] == pytest.approx(expected)

    @pytest.mark.parametrize("bad_value", ["N/A", "n/d", "#REF!", "", "   "])
    def test_invalid_values_drop_row(self, bad_value):
        """Rows with unparseable values must be dropped (value is a critical column)."""
        df = transform_valid(value=bad_value)
        assert len(df) == 0

    def test_zero_value_is_kept(self):
        """Zero is a valid financial value and must not be filtered out."""
        df = transform_valid(value="0,00")
        assert len(df) == 1
        assert df["value"][0] == pytest.approx(0.0)

    def test_large_value_precision(self):
        df = transform_valid(value="999.999.999,99")
        assert df["value"][0] == pytest.approx(999_999_999.99)

    def test_value_column_is_float64(self):
        df = transform_valid(value="1.000,00")
        assert df["value"].dtype == pl.Float64


# ---------------------------------------------------------------------------
# Date normalization
# ---------------------------------------------------------------------------

class TestDateNormalization:
    @pytest.mark.parametrize("raw, expected", [
        ("31/12/2023", "2023-12-31"),
        ("01/01/2014", "2014-01-01"),
        ("15-06-2020", "2020-06-15"),
        ("2019-03-31", "2019-03-31"),
        ("20180101",   "2018-01-01"),
    ])
    def test_date_formats(self, raw, expected):
        df = transform_valid(date=raw)
        assert df["date"][0] == expected

    def test_invalid_date_becomes_null_and_row_survives(self):
        """date is NOT a critical column — row is kept with null date."""
        df = transform_valid(date="not-a-date")
        assert len(df) == 1
        assert df["date"][0] is None

    def test_date_output_is_string(self):
        df = transform_valid(date="31/12/2023")
        assert df["date"].dtype == pl.Utf8


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

class TestDeduplication:
    def test_intra_chunk_duplicates_removed(self):
        rows = [
            {**{"sector_code":"22","entity_type":"X","ruc":"0991290915001",
                "company_name":"A","date":"31/12/2023","period_type":"ANUAL",
                "account_code":"1","account_name":"ACTIVO","value":"100,00"}},
            {**{"sector_code":"22","entity_type":"X","ruc":"0991290915001",
                "company_name":"A","date":"31/12/2023","period_type":"ANUAL",
                "account_code":"1","account_name":"ACTIVO","value":"200,00"}},
        ]
        df = transform(rows)
        assert len(df) == 1

    def test_same_account_different_period_type_both_kept(self):
        """ANUAL and MENSUAL records for the same account+date are distinct."""
        rows = [
            {**{"sector_code":"22","entity_type":"X","ruc":"0991290915001",
                "company_name":"A","date":"31/12/2023","period_type":"ANUAL",
                "account_code":"1","account_name":"ACTIVO","value":"100,00"}},
            {**{"sector_code":"22","entity_type":"X","ruc":"0991290915001",
                "company_name":"A","date":"31/12/2023","period_type":"MENSUAL",
                "account_code":"1","account_name":"ACTIVO","value":"100,00"}},
        ]
        df = transform(rows)
        assert len(df) == 2

    def test_different_companies_both_kept(self):
        rows = [
            {**{"sector_code":"22","entity_type":"X","ruc":"0000000000001",
                "company_name":"A","date":"31/12/2023","period_type":"ANUAL",
                "account_code":"1","account_name":"ACTIVO","value":"100,00"}},
            {**{"sector_code":"22","entity_type":"X","ruc":"0000000000002",
                "company_name":"B","date":"31/12/2023","period_type":"ANUAL",
                "account_code":"1","account_name":"ACTIVO","value":"200,00"}},
        ]
        df = transform(rows)
        assert len(df) == 2

    def test_different_account_codes_both_kept(self):
        rows = [
            {**{"sector_code":"22","entity_type":"X","ruc":"0991290915001",
                "company_name":"A","date":"31/12/2023","period_type":"ANUAL",
                "account_code":"1","account_name":"ACTIVO","value":"100,00"}},
            {**{"sector_code":"22","entity_type":"X","ruc":"0991290915001",
                "company_name":"A","date":"31/12/2023","period_type":"ANUAL",
                "account_code":"2","account_name":"PASIVO","value":"50,00"}},
        ]
        df = transform(rows)
        assert len(df) == 2


# ---------------------------------------------------------------------------
# Critical column null handling
# ---------------------------------------------------------------------------

class TestNullHandling:
    def test_null_ruc_drops_row(self):
        df = transform_valid(ruc="")
        assert len(df) == 0

    def test_null_account_code_drops_row(self):
        df = transform_valid(account_code="")
        assert len(df) == 0

    def test_null_value_drops_row(self):
        df = transform_valid(value="")
        assert len(df) == 0

    def test_null_non_critical_column_keeps_row(self):
        """Missing company_name or account_name must not drop the row."""
        df = transform_valid(company_name="", account_name="")
        assert len(df) == 1

    def test_entirely_empty_chunk_returns_empty_df(self):
        rows = [{"sector_code":"","entity_type":"","ruc":"","company_name":"",
                 "date":"","period_type":"","account_code":"","account_name":"","value":""}]
        df = transform(rows)
        assert len(df) == 0


# ---------------------------------------------------------------------------
# Whitespace stripping
# ---------------------------------------------------------------------------

class TestWhitespaceStripping:
    def test_strips_leading_trailing_spaces_from_ruc(self):
        df = transform_valid(ruc="  0991290915001  ")
        assert df["ruc"][0] == "0991290915001"

    def test_strips_spaces_from_company_name(self):
        df = transform_valid(company_name="  FUTURFID S.A.  ")
        assert df["company_name"][0] == "FUTURFID S.A."

    def test_strips_spaces_from_account_code(self):
        df = transform_valid(account_code="  1  ")
        assert df["account_code"][0] == "1"

    def test_strips_spaces_from_value_before_parsing(self):
        df = transform_valid(value="  1.000,00  ")
        assert df["value"][0] == pytest.approx(1000.0)
