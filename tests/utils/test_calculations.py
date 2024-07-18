"""Tests for the calculations module."""

import math

import pytest

from cg.utils.calculations import (
    divide_by_thousand_with_one_decimal,
    fraction_to_percent,
    multiply_by_million,
)


def test_divide_by_thousand_with_one_decimal():
    # GIVEN a number
    number: float = 1_234.00

    # WHEN dividing by a thousand
    divided: float = divide_by_thousand_with_one_decimal(number)

    # THEN the number should be divided by a thousand and only one decimal should be kept
    assert math.isclose(divided, 1.2, abs_tol=1e-9)


@pytest.mark.parametrize(
    "fraction, expected",
    [
        (0.50, 50.00),
        (0.001, 0.1),
        (2, 2),
    ],
)
def test_fraction_to_percent(fraction: float, expected: float):
    # GIVEN a fraction

    # WHEN converting the fraction to a percentage
    percentage: float = fraction_to_percent(fraction)

    # THEN the fraction should be converted to a percentage
    assert math.isclose(percentage, expected, abs_tol=1e-9)


def test_multiple_by_a_million():
    # GIVEN a number
    number: float = 1.00

    # WHEN multiplying by a million
    multiplied: int = multiply_by_million(number)

    # THEN the number should be multiplied by a million
    assert multiplied == int(number * 1_000_000)
