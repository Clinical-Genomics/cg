"""Module to handle dictionary helper functions."""

from typing import List, Dict


def get_list_from_dictionary(dictionary: Dict) -> list:
    """Return a list of the passed dict non-empty key values."""
    list_from_dict: List[str] = []
    for key, value in dictionary.items():
        if value:
            list_from_dict.extend([key, value])
    return list_from_dict


def get_full_path_dictionary(dictionary: Dict) -> dict:
    """Return a full path of the values of the passed dictionary."""
    full_path_dict: dict = {}
    for key, value in dictionary.items():
        full_path_dict[key] = value.full_path if value else None

    return full_path_dict
