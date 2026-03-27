"""
Tests for etl/extract.py — column assignment, error handling, chunked reading.
"""

import pytest
import polars as pl

from etl.extract import COLUMN_NAMES, _assign_column_names, iter_csv_chunks
from tests.conftest import sample_tsv   # noqa: F401 (used as fixture)


# ---------------------------------------------------------------------------
# _assign_column_names
# ---------------------------------------------------------------------------

class TestAssignColumnNames:
    def _make_df(self, n_cols: int) -> pl.DataFrame:
        """Build a DataFrame with n_cols generic string columns."""
        return pl.DataFrame(
            {f"column_{i+1}": ["x"] for i in range(n_cols)}
        )

    def test_renames_to_expected_names(self):
        df = self._make_df(len(COLUMN_NAMES))
        result = _assign_column_names(df)
        assert result.columns == COLUMN_NAMES

    def test_drops_trailing_columns(self):
        """TSV files have a trailing empty 10th column — it must be discarded."""
        df = self._make_df(len(COLUMN_NAMES) + 3)
        result = _assign_column_names(df)
        assert result.columns == COLUMN_NAMES
        assert len(result.columns) == len(COLUMN_NAMES)

    def test_raises_when_too_few_columns(self):
        df = self._make_df(len(COLUMN_NAMES) - 1)
        with pytest.raises(ValueError, match="se esperaban al menos"):
            _assign_column_names(df)

    def test_all_expected_columns_present(self):
        df = self._make_df(len(COLUMN_NAMES))
        result = _assign_column_names(df)
        for col in ["sector_code", "ruc", "account_code", "value", "date", "period_type"]:
            assert col in result.columns


# ---------------------------------------------------------------------------
# iter_csv_chunks
# ---------------------------------------------------------------------------

class TestIterCsvChunks:
    def test_raises_on_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            list(iter_csv_chunks(tmp_path / "nonexistent.tsv", chunk_size=100))

    def test_reads_all_rows(self, sample_tsv):
        chunks = list(iter_csv_chunks(sample_tsv, chunk_size=1_000))
        total = sum(len(df) for _, df in chunks)
        assert total == 6

    def test_chunk_numbers_are_sequential(self, sample_tsv):
        chunk_nums = [n for n, _ in iter_csv_chunks(sample_tsv, chunk_size=1_000)]
        assert chunk_nums == list(range(1, len(chunk_nums) + 1))

    def test_columns_match_expected(self, sample_tsv):
        _, df = next(iter_csv_chunks(sample_tsv, chunk_size=1_000))
        assert df.columns == COLUMN_NAMES

    def test_small_chunk_size_yields_multiple_chunks(self, sample_tsv):
        """chunk_size=1 must yield one chunk per row."""
        chunks = list(iter_csv_chunks(sample_tsv, chunk_size=1))
        assert len(chunks) == 6

    def test_all_values_are_strings_after_read(self, sample_tsv):
        """infer_schema_length=0 means every column must be Utf8."""
        _, df = next(iter_csv_chunks(sample_tsv, chunk_size=1_000))
        non_utf8 = [c for c in df.columns if df[c].dtype != pl.Utf8]
        assert non_utf8 == [], f"Non-Utf8 columns after extraction: {non_utf8}"
