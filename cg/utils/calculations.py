"""Module to hold functions for calculations."""


def fraction_to_percent(value: float) -> float:
    """Convert a fraction to a percentage."""
    if 0.0 <= value <= 1.0:
        value *= 100
    return value


def multiply_by_million(number: float | int) -> int:
    """Multiply a given number by a million."""
    return int(number * 1_000_000)
