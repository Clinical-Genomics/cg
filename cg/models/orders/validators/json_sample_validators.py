from typing import Any


def join_list(potential_list: Any):
    """If given a list, it is converted to a string by joining its entries.
    Else the argument is returned as is. Used here to convert any provided synopsis to a string."""
    return "".join(potential_list) if isinstance(potential_list, list) else potential_list


def convert_well(value: str):
    """Forces the format of the well position to separate rows and values with a ':', e.g. A:8, C:3 etc."""
    if not value:
        return None
    return value if ":" in value else ":".join([value[0], value[1:]])
