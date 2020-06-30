"""Class with small helper functions"""

from typing import Iterable


class SmallHelpers:
    """Hold small methods that might be helpful for the tests"""

    @staticmethod
    def length_of_iterable(iter_obj: Iterable) -> int:
        """Returns the length of an iterable"""
        return sum(1 for _ in iter_obj)
