"""Module to hold functions for calculations."""


def divide_by_thousand_with_one_decimal(number: float | int) -> float:
    return round(number / 1_000, 1)


def fraction_to_percent(value: float) -> float:
    """Convert a fraction to a percentage."""
    if 0.0 <= value <= 1.0:
        value *= 100
    return value


def multiply_by_million(number: float | int) -> int:
    """Multiply a given number by a million."""
    return int(number * 1_000_000)
