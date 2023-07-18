"""Helper functions."""

from pathlib import Path
from typing import List, Optional


def get_string_from_list_by_pattern(strings: List[str], pattern: str) -> Optional[str]:
    """Returns the full string from a list given a specific pattern."""

    return next((string for string in strings if pattern in string), None) if strings else None


def build_command_from_dict(options: dict, exclude_true: bool = False) -> List[str]:
    """Returns a command list of strings given a dictionary with arguments."""
    formatted_options: list = []
    for option_name, option_value in options.items():
        if option_value:
            if exclude_true and option_value is True:
                formatted_options.append(str(option_name))
            elif option_value:
                formatted_options.append(str(option_name))
                formatted_options.append(str(option_value))
    return formatted_options


def get_hamming_distance(str_1: str, str_2: str) -> int:
    """Return the hamming distance between two strings.

    Raises:
        KeyError: When the strings have the same length.
    """
    if len(str_1) != len(str_2):
        raise KeyError("The two strings must have the same length to calculate distance!")
    return sum(n1 != n2 for n1, n2 in zip(str_1, str_2))
