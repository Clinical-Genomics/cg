"""Class with small helper functions"""

from typing import Iterable


class SmallHelpers:
    """Hold small methods that might be helpful for the tests"""

    @staticmethod
    def length_of_iterable(iter_obj: Iterable) -> int:
        """Returns the length of an iterable"""
        return sum(1 for _ in iter_obj)

    @staticmethod
    def length_of_nested_list(nested_list: list[list]) -> int:
        """Returns the length of a nested list"""
        return sum(1 for _ in nested_list for _ in _)
