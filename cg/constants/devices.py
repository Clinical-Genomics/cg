"""Enums for run_devices."""

from enum import Enum, StrEnum, auto


class DeviceType(Enum):
    ILLUMINA = auto()
    BIONANO = auto()
    OXFORD_NANOPORE = auto()
    PACBIO = auto()


class RevioNames(StrEnum):
    BETTY = "Betty"
    WILMA = "Wilma"
