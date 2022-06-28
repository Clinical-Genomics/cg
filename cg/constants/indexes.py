"""Constants for accessing elements in arrays"""
from enum import Enum


class ListIndexes(Enum):
    """indexes used when accessing elements of a list"""

    FIRST: int = 0
    LAST: int = -1
    PDC_FC_COLUMN: int = 9
    PDC_KEY_COLUMN: int = 20
