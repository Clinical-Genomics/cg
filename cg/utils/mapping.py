"""Util functions that provide support in mapping objects."""

import re
from cg.exc import CgError


def get_item_by_pattern(pattern: str, pattern_map: dict[str, any]) -> any:
    """
    Check if the pattern is in the keys of the pattern map.
    Raises an CgError.
    """
    for map_key in pattern_map.keys():
        if re.search(map_key, pattern):
            return pattern_map.get(map_key)
    raise CgError(f"Could not find pattern for {pattern} in {pattern_map.keys()}.")
