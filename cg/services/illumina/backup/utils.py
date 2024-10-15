"""Helper functions."""

from datetime import datetime
from operator import attrgetter

from cg.constants import FileExtensions
from cg.services.illumina.backup.exc import (
    DsmcMissingEncryptionKeyError,
    DsmcMissingSequenceFileError,
)
from cg.services.illumina.backup.models import DsmcEncryptionKey, DsmcSequencingFile


class DsmcOutput:
    DATE_COLUMN_INDEX = 2
    TIME_COLUMN_INDEX = 3
    PATH_COLUMN_INDEX = 4


def is_dsmc_encryption_key(line: str) -> bool:
    return (
        FileExtensions.KEY in line
        and FileExtensions.GPG in line
        and FileExtensions.GZIP not in line
    )


def is_dsmc_sequencing_path(line: str) -> bool:
    return FileExtensions.TAR in line and FileExtensions.GZIP in line and FileExtensions.GPG in line


def get_latest_dsmc_archived_sequencing_run(
    dsmc_files: list[DsmcSequencingFile],
) -> DsmcSequencingFile:
    """Return the latest file path based on the date attribute."""

    if not dsmc_files:
        raise DsmcMissingSequenceFileError("No archived sequencing in DSMC output.")

    latest_file = max(dsmc_files, key=attrgetter("dateTime"))

    return latest_file


def get_latest_dsmc_encryption_key(dsmc_files: list[DsmcEncryptionKey]) -> DsmcEncryptionKey:
    """Return the latest file path based on the date attribute."""

    if not dsmc_files:
        raise DsmcMissingEncryptionKeyError("No Encryption Key in DSMC output.")

    latest_file = max(dsmc_files, key=attrgetter("dateTime"))

    return latest_file


def convert_string_to_datetime_object(strDateTime: str) -> datetime:
    date_formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
        "%m/%d/%Y %H:%M:%S",
    ]

    for fmt in date_formats:
        try:
            return datetime.strptime(strDateTime, fmt)
        except ValueError:
            continue

    raise ValueError(f"Could not convert '{strDateTime}' to a datetime object.")
