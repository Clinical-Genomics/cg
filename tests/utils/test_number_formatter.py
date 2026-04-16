import pytest

from cg.utils.number_formatter import Si

_ = "\u202f"


@pytest.mark.parametrize(
    "value,unit,expected",
    [
        # Integers
        (-1e6, "", f"-1000000{_}"),
        (-1e3, "", f"-1000{_}"),
        (-999, "", f"-999{_}"),
        (-1, "", f"-1{_}"),
        (0, "", f"0{_}"),
        (1, "", f"1{_}"),
        (999, "", f"999{_}"),
        (1000, "", f"1.00{_}k"),
        (1005, "", f"1.00{_}k"),
        (1006, "", f"1.01{_}k"),
        (999 * 1e3, "", f"999.00{_}k"),
        (1000 * 1e3, "", f"1.00{_}M"),
        (1005 * 1e3, "", f"1.00{_}M"),
        (1006 * 1e3, "", f"1.01{_}M"),
        (999 * 1e6, "", f"999.00{_}M"),
        (1000 * 1e6, "", f"1.00{_}G"),
        (1005 * 1e6, "", f"1.00{_}G"),
        (1006 * 1e6, "", f"1.01{_}G"),
        (999 * 1e9, "", f"999.00{_}G"),
        (1000 * 1e9, "", f"1.00{_}T"),
        (1005 * 1e9, "", f"1.00{_}T"),
        (1006 * 1e9, "", f"1.01{_}T"),
        (1e15, "", f"1000.00{_}T"),
        # Float
        (-1e6 + 0.0, "", f"-1000000{_}"),
        (-1e3 + 0.0, "", f"-1000{_}"),
        (-999.0, "", f"-999{_}"),
        (-1.0, "", f"-1{_}"),
        (0.0, "", f"0{_}"),
        (1.0, "", f"1{_}"),
        (1e3 + 0.0, "", f"1.00{_}k"),
        (1e6 + 0.0, "", f"1.00{_}M"),
        (1e9 + 0.0, "", f"1.00{_}G"),
        (1e12 + 0.0, "", f"1.00{_}T"),
        (1e15 + 0.0, "", f"1000.00{_}T"),
    ],
)
def test_prefix_integer_no_unit(value, unit, expected):
    # GIVEN values
    # WHEN formatting
    # THEN formatting should be according to SI, 9th edition
    assert Si.prefix(value=value, unit=unit) == expected


@pytest.mark.parametrize(
    "value,unit,expected",
    [
        # Integers
        (-1e3, "b", f"-1000{_}b"),
        (-1, "b", f"-1{_}b"),
        (0, "b", f"0{_}b"),
        (1, "b", f"1{_}b"),
        (1e3, "b", f"1.00{_}kb"),
        (1e6, "b", f"1.00{_}Mb"),
        (1e9, "b", f"1.00{_}Gb"),
        (1e12, "b", f"1.00{_}Tb"),
        (1e15, "b", f"1000.00{_}Tb"),
        # Floats
        (-1e3 + 0.0, "b", f"-1000{_}b"),
        (-1.0, "b", f"-1{_}b"),
        (0.0, "b", f"0{_}b"),
        (1.0, "b", f"1{_}b"),
        (1e3 + 0.0, "b", f"1.00{_}kb"),
        (1e6 + 0.0, "b", f"1.00{_}Mb"),
        (1e9 + 0.0, "b", f"1.00{_}Gb"),
        (1e12 + 0.0, "b", f"1.00{_}Tb"),
        (1e15 + 0.0, "b", f"1000.00{_}Tb"),
    ],
)
def test_prefix_unit(value, unit, expected):
    # GIVEN values (ints and floats)
    # WHEN formatting
    # THEN formatting should be according to SI, 9th edition
    assert Si.prefix(value=value, unit=unit) == expected


@pytest.mark.parametrize(
    "value,expected",
    [
        (-1e15, f"-1{_}000{_}000{_}000{_}000{_}000"),
        (-1e12, f"-1{_}000{_}000{_}000{_}000"),
        (-1e9, f"-1{_}000{_}000{_}000"),
        (-1e6, f"-1{_}000{_}000"),
        (-1e3, f"-1{_}000"),
        (-1, "-1"),
        (0, "0"),
        (1, "1"),
        (1e3, f"1{_}000"),
        (1e6, f"1{_}000{_}000"),
        (1e9, f"1{_}000{_}000{_}000"),
        (1e12, f"1{_}000{_}000{_}000{_}000"),
        (1e15, f"1{_}000{_}000{_}000{_}000{_}000"),
        (0.0, "0"),
        (1.0, "1"),
        (1e3 + 0.0, f"1{_}000"),
        (1e6 + 0.0, f"1{_}000{_}000"),
        (1e9 + 0.0, f"1{_}000{_}000{_}000"),
        (1e12 + 0.0, f"1{_}000{_}000{_}000{_}000"),
        (1e15 + 0.0, f"1{_}000{_}000{_}000{_}000{_}000"),
    ],
)
def test_si_group_digits(value, expected):
    # GIVEN values (ints and floats)
    # WHEN formatting
    # THEN formatting should be according to SI, 9th edition
    assert Si.group_digits(value=value) == expected
