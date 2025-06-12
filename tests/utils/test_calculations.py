"""Tests for the calculations module."""

import math

import pytest

from cg.utils.calculations import fraction_to_percent, multiply_by_million


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
