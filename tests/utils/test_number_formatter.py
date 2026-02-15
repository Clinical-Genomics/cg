import pytest

from cg.utils.number_formatter import Si


def test_Si_prefix_discrete_value_no_unit_int_and_float():
    # GIVEN values (ints and floats)
    # WHEN formatting
    # THEN formatting should be according to SI, 9th edition

    # Integers
    assert Si.prefix(value=0, unit="") == "0\u202f"
    assert Si.prefix(value=1, unit="") == "1\u202f"
    assert Si.prefix(value=1e3, unit="") == "1.00\u202fk"
    assert Si.prefix(value=1e6, unit="") == "1.00\u202fM"
    assert Si.prefix(value=1e9, unit="") == "1.00\u202fG"
    assert Si.prefix(value=1e12, unit="") == "1.00\u202fT"
    assert Si.prefix(value=1e15, unit="") == "1000.00\u202fT"

    # Floats (should behave the same)
    assert Si.prefix(value=0.0, unit="") == "0\u202f"
    assert Si.prefix(value=1.0, unit="") == "1\u202f"
    assert Si.prefix(value=1e3 + 0.0, unit="") == "1.00\u202fk"
    assert Si.prefix(value=1e6 + 0.0, unit="") == "1.00\u202fM"
    assert Si.prefix(value=1e9 + 0.0, unit="") == "1.00\u202fG"
    assert Si.prefix(value=1e12 + 0.0, unit="") == "1.00\u202fT"


def test_Si_prefix_discrete_value_unit_int_and_float():
    # GIVEN values (ints and floats)
    # WHEN formatting
    # THEN formatting should be according to SI, 9th edition

    # Integers
    assert Si.prefix(value=0, unit="b") == "0\u202fb"
    assert Si.prefix(value=1, unit="b") == "1\u202fb"
    assert Si.prefix(value=1e3, unit="b") == "1.00\u202fkb"
    assert Si.prefix(value=1e6, unit="b") == "1.00\u202fMb"
    assert Si.prefix(value=1e9, unit="b") == "1.00\u202fGb"
    assert Si.prefix(value=1e12, unit="b") == "1.00\u202fTb"

    # Floats
    assert Si.prefix(value=0.0, unit="b") == "0\u202fb"
    assert Si.prefix(value=1.0, unit="b") == "1\u202fb"
    assert Si.prefix(value=1e3 + 0.0, unit="b") == "1.00\u202fkb"
    assert Si.prefix(value=1e6 + 0.0, unit="b") == "1.00\u202fMb"
    assert Si.prefix(value=1e9 + 0.0, unit="b") == "1.00\u202fGb"
    assert Si.prefix(value=1e12 + 0.0, unit="b") == "1.00\u202fTb"


def test_Si_group_digits_discrete_value_int_and_float():
    # GIVEN values (ints and floats)
    # WHEN formatting
    # THEN formatting should be according to SI, 9th edition

    # Integers
    assert Si.group_digits(value=0) == "0"
    assert Si.group_digits(value=1) == "1"
    assert Si.group_digits(value=1e3) == "1\u202f000"
    assert Si.group_digits(value=1e6) == "1\u202f000\u202f000"
    assert Si.group_digits(value=1e9) == "1\u202f000\u202f000\u202f000"
    assert Si.group_digits(value=1e12) == "1\u202f000\u202f000\u202f000\u202f000"
    assert Si.group_digits(value=1e15) == "1\u202f000\u202f000\u202f000\u202f000\u202f000"

    # Floats (should behave identically)
    assert Si.group_digits(value=0.0) == "0"
    assert Si.group_digits(value=1.0) == "1"
    assert Si.group_digits(value=1e3 + 0.0) == "1\u202f000"
    assert Si.group_digits(value=1e6 + 0.0) == "1\u202f000\u202f000"
    assert Si.group_digits(value=1e9 + 0.0) == "1\u202f000\u202f000\u202f000"
    assert Si.group_digits(value=1e12 + 0.0) == "1\u202f000\u202f000\u202f000\u202f000"
    assert Si.group_digits(value=1e15 + 0.0) == "1\u202f000\u202f000\u202f000\u202f000\u202f000"


@pytest.mark.parametrize(
    "input_value,expected",
    [
        (0.0, 0),
        (0.4, 0),
        (0.5, 1),
        (1.2, 1),
        (1.5, 2),
        (1234.4, 1234),
        (1234.5, 1235),
        (1e6 + 0.49, 1_000_000),
        (1e6 + 0.5, 1_000_001),
    ],
)
def test_validate_discrete_rounding(input_value, expected):
    assert Si._integer_convert(input_value) == expected
