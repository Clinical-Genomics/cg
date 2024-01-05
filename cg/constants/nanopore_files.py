"""Constants related to Oxford Nanopore sequencing."""
from enum import StrEnum


class NanoporeDirsAndFiles(StrEnum):
    """Holds file and directory names for nanopore sequencing output."""

    DATA_DIRECTORY: str = "nanopore"
    SYSTEMD_TRIGGER_DIRECTORY: str = "trigger_directory"
