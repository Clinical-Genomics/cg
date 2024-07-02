"""Module to handle dictionary helper functions."""


def remove_duplicate_dicts(dicts: list[dict]) -> list[dict]:
    return [
        dict(dictionary_tuple)
        for dictionary_tuple in {tuple(dictionary.items()) for dictionary in dicts}
    ]


def get_list_from_dictionary(dictionary: dict) -> list:
    """Return a list of the passed dict non-empty key values."""
    list_from_dict: list[str] = []
    for key, value in dictionary.items():
        if value:
            list_from_dict.extend([key, value])
    return list_from_dict


def get_full_path_dictionary(dictionary: dict) -> dict:
    """Return a full path of the values of the passed dictionary."""
    return {key: value.full_path if value else None for key, value in dictionary.items()}
