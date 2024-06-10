"""Enums for run_devices."""

from enum import Enum, auto


class DeviceType(Enum):
    ILLUMINA = auto()
    BIONANO = auto()
    OXFORD_NANOPORE = auto()
    PACBIO = auto()
