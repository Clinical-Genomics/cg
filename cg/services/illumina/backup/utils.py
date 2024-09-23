"""Helper functions."""

from enum import IntEnum
from pathlib import Path

from cg.constants import FileExtensions
from cg.exc import ValidationError
from cg.services.illumina.file_parsing.models import (
    DsmcEncryptionKey,
    DsmcSequencingFile,
)
from cg.constants import FileExtensions


class DsmcOutput:
    DATE_COLUMN_INDEX = 2
    TIME_COLUMN_INDEX = 3
    PATH_COLUMN_INDEX = 4


def contains_dsmc_key(line: str) -> bool:
    if (
        FileExtensions.KEY in line
        and FileExtensions.GPG in line
        and FileExtensions.GZIP not in line
    ):
        return True
    return False


def contains_dsmc_sequencing_path(line: str) -> bool:
    if FileExtensions.TAR in line and FileExtensions.GZIP in line and FileExtensions.GPG in line:
        return True
    return False


def get_latest_dsmc_archived_sequencing_run(dsmc_files: list[DsmcSequencingFile]) -> Path:
    """Return the latest file path based on the date attribute."""
    if not dsmc_files:
        return None  # Return None if the list is empty

    # Get the file with the latest date
    latest_file = max(dsmc_files, key=lambda file: file.date)

    # Return the sequencing_path as a Path object
    return Path(latest_file.sequencing_path)


def get_latest_dsmc_encryption_key(dsmc_files: list[DsmcEncryptionKey]) -> Path:
    """Return the latest file path based on the date attribute."""
    if not dsmc_files:
        return None  # Return None if the list is empty

    # Get the file with the latest date
    latest_file = max(dsmc_files, key=lambda file: file.date)

    # Return the sequencing_path as a Path object
    return Path(latest_file.key_path)
