"""Helper functions."""

from typing import Optional, List


def get_string_from_list_by_pattern(list_of_strings: List[str], pattern: str) -> Optional[str]:
    """Returns the full string from a list given a specific pattern."""

    return (
        next((value for value in list_of_strings if pattern in value), None)
        if list_of_strings
        else None
    )
