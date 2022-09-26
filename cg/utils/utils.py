"""Helper functions."""

from typing import Optional, List, Any


def get_string_from_list_by_pattern(pattern: str, collection: List[str]) -> Optional[str]:
    """Returns the full string from a list given a specific pattern."""

    return next((value for value in collection if pattern in value), None)


def get_last_element_from_iterator(iterator: iter) -> Optional[Any]:
    """Retrieves the last item from an iterator object."""

    item = None
    for item in iterator:
        continue

    return item
