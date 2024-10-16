from pathlib import Path

from cg.constants import FileExtensions
from cg.exc import MissingFilesError


def is_valid_pdc_encryption_key_path(value: Path) -> Path:
    if not value.name.endswith(f"{FileExtensions.KEY}{FileExtensions.GPG}"):
        raise MissingFilesError("Missing a valid encryption key.")
    return value


def is_valid_pdc_sequencing_file_path(value: Path) -> Path:
    if not value.name.endswith(f"{FileExtensions.TAR}{FileExtensions.GZIP}{FileExtensions.GPG}"):
        raise MissingFilesError("Missing a valid sequence file.")
    return value
