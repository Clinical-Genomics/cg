"""Module to handle dictionary helper functions."""

from typing import List


def get_list_from_dictionary(dictionary: dict) -> list:
    """Returns a list of the passed dict non-empty key values."""
    list_from_dict: List[str] = []
    for key, value in dictionary.items():
        if value:
            list_from_dict.extend([key, value])
    return list_from_dict
