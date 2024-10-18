"""Helper functions for the back-up of Illumina flow cells."""

from operator import attrgetter

from cg.constants import FileExtensions
from cg.services.illumina.backup.models import PdcEncryptionKey, PdcSequencingFile


class DsmcOutput:
    DATE_COLUMN_INDEX = 2
    TIME_COLUMN_INDEX = 3
    PATH_COLUMN_INDEX = 4


def is_pdc_encryption_key(line: str) -> bool:
    return (
        FileExtensions.KEY in line
        and FileExtensions.GPG in line
        and FileExtensions.GZIP not in line
    )


def is_pdc_sequencing_path(line: str) -> bool:
    return FileExtensions.TAR in line and FileExtensions.GZIP in line and FileExtensions.GPG in line


def get_latest_pdc_archived_sequencing_run(
    pdc_files: list[PdcSequencingFile],
) -> PdcSequencingFile | None:
    """Return the most recent sequencing run based on the 'dateTime' attribute, or None if no files are present."""

    if not pdc_files:
        return None

    latest_file = max(pdc_files, key=attrgetter("dateTime"))

    return latest_file


def get_latest_pdc_encryption_key(pdc_files: list[PdcEncryptionKey]) -> PdcEncryptionKey | None:
    """Return the most recent encryption key based on the 'dateTime' attribute, or None if no keys are present."""

    if not pdc_files:
        return None

    latest_file = max(pdc_files, key=attrgetter("dateTime"))

    return latest_file
