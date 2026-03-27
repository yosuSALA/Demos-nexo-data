import pytest
from utils.formatters import parse_ec_number, normalize_date


@pytest.mark.parametrize("raw, expected", [
    ("1.188.854,66",  1_188_854.66),
    ("1.000,00",      1_000.00),
    ("500,75",        500.75),
    ("1000",          1000.0),
    ("-2.500,30",     -2_500.30),
    ("",              None),
    ("N/A",           None),
    (None,            None),
])
def test_parse_ec_number(raw, expected):
    assert parse_ec_number(raw) == expected


@pytest.mark.parametrize("raw, expected", [
    ("31/12/2023",  "2023-12-31"),
    ("01-06-2022",  "2022-06-01"),
    ("2021-03-15",  "2021-03-15"),
    ("20200101",    "2020-01-01"),
    ("",            None),
    (None,          None),
    ("not-a-date",  None),
])
def test_normalize_date(raw, expected):
    assert normalize_date(raw) == expected
