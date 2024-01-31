"""Enum classes has string or list values that behaves like defined """

from enum import Enum


class ListEnum(list, Enum):
    pass
