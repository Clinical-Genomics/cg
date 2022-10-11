"""Module to handle formatting functions."""


def get_flattened_dictionary(dictionary: dict) -> list:
    """Takes a dictionary and returns a list of its non-empty elements flattened into a list."""
    populated_dict = {param: value for param, value in dictionary.items() if value}
    return [item for sublist in populated_dict.items() for item in sublist]
