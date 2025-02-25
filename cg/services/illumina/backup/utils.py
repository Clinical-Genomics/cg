"""Helper functions for the back-up of Illumina flow cells."""

from datetime import datetime
from operator import attrgetter
from pathlib import Path

from cg.constants import FileExtensions
from cg.meta.backup.backup import LOG
from cg.services.illumina.backup.models import PdcEncryptionKey, PdcSequencingFile
from cg.utils.date import convert_string_to_datetime_object


class DsmcOutput:
    DATE_COLUMN_INDEX = 2
    TIME_COLUMN_INDEX = 3
    PATH_COLUMN_INDEX = 4


def get_latest_archived_sequencing_run_path(dsmc_output: list[str]) -> Path | None:
    """Get the path of the archived sequencing run from a PDC query."""
    validated_sequencing_paths: list[PdcSequencingFile] = _parse_dsmc_output_sequencing_path(
        dsmc_output
    )
    archived_run: PdcSequencingFile | None = _get_latest_sequencing_run_in_list(
        validated_sequencing_paths
    )
    if archived_run:
        LOG.info(f"Sequencing run found: {archived_run}")
        return archived_run.path


def get_latest_archived_encryption_key_path(dsmc_output: list[str]) -> Path | None:
    """Get the encryption key for the archived sequencing run from a PDC query."""
    validated_encryption_keys: list[PdcEncryptionKey] = _parse_dsmc_output_key_path(dsmc_output)

    archived_encryption_key: PdcEncryptionKey | None = _get_latest_pdc_encryption_key(
        validated_encryption_keys
    )
    if archived_encryption_key:
        LOG.info(f"Encryption key found: {archived_encryption_key}")
        return archived_encryption_key.path


def _parse_dsmc_output_sequencing_path(dsmc_output: list[str]) -> list[PdcSequencingFile]:
    """Parses the DSMC command output to extract validated sequencing paths."""
    validated_responses: list[PdcSequencingFile] = []
    for line in dsmc_output:
        if is_pdc_sequencing_path(line):
            parts: list[str] = line.split()

            file_date_time: datetime = convert_string_to_datetime_object(
                f"{parts[DsmcOutput.DATE_COLUMN_INDEX]} {parts[DsmcOutput.TIME_COLUMN_INDEX]}"
            )

            query_response = PdcSequencingFile(
                date_time=file_date_time,
                path=Path(parts[DsmcOutput.PATH_COLUMN_INDEX]),
            )
            validated_responses.append(query_response)

    return validated_responses


def _parse_dsmc_output_key_path(dsmc_output: list[str]) -> list[PdcEncryptionKey]:
    """Parses the DSMC command output to extract validated encryption keys."""
    validated_responses: list[PdcEncryptionKey] = []
    for line in dsmc_output:
        if is_pdc_encryption_key(line):
            parts: list[str] = line.split()

            file_date_time: datetime = convert_string_to_datetime_object(
                f"{parts[DsmcOutput.DATE_COLUMN_INDEX]} {parts[DsmcOutput.TIME_COLUMN_INDEX]}"
            )

            query_response = PdcEncryptionKey(
                date_time=file_date_time,
                path=Path(parts[DsmcOutput.PATH_COLUMN_INDEX]),
            )

            validated_responses.append(query_response)

    return validated_responses


def _get_latest_sequencing_run_in_list(
    pdc_files: list[PdcSequencingFile],
) -> PdcSequencingFile | None:
    """Return the most recent sequencing run based on the 'dateTime' attribute, or None if no files are present."""

    if not pdc_files:
        return None

    latest_file: PdcSequencingFile | None = max(pdc_files, key=attrgetter("date_time"))

    return latest_file


def _get_latest_pdc_encryption_key(pdc_files: list[PdcEncryptionKey]) -> PdcEncryptionKey | None:
    """Return the latest encryption key or None if no keys are present."""

    if not pdc_files:
        return None

    latest_file: PdcEncryptionKey | None = max(pdc_files, key=attrgetter("date_time"))

    return latest_file


def is_pdc_sequencing_path(line: str) -> bool:
    return FileExtensions.TAR in line and FileExtensions.GZIP in line and FileExtensions.GPG in line


def is_pdc_encryption_key(line: str) -> bool:
    return (
        FileExtensions.KEY in line
        and FileExtensions.GPG in line
        and FileExtensions.GZIP not in line
    )
