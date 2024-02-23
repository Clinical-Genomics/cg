"""Tests for the calculations module."""

from cg.utils.calculations import multiply_by_million


def test_multiple_by_a_million():
    # GIVEN a number
    number: float = 1.00

    # WHEN multiplying by a million
    multiplied: int = multiply_by_million(number)

    # THEN the number should be multiplied by a million
    assert multiplied == int(number * 1_000_000)
