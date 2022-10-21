"""Helper functions."""

from typing import Optional, List


def get_string_from_list_by_pattern(strings: List[str], pattern: str) -> Optional[str]:
    """Returns the full string from a list given a specific pattern."""

    return next((string for string in strings if pattern in string), None) if strings else None
