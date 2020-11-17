""" string enum class has string values that behaves like defined """
from enum import Enum


class StrEnum(str, Enum):
    def __str__(self) -> str:
        return str.__str__(self)
