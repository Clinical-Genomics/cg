"""Enums for devices."""

from enum import Enum, auto


class DeviceType(Enum):
    ILLUMINA = auto()
    SEPHYR = auto()
    OXFORD_NANOPORE = auto()
    PACBIO = auto()
