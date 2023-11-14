"""Module to hold functions for calculations."""


def multiply_by_million(number: float | int) -> int:
    """Multiply a given number by a million."""
    return int(number * 1_000_000)
