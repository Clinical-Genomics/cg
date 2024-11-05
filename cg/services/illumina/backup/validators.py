from pathlib import Path

from cg.constants import FileExtensions
from cg.exc import ValidationError


def validated_pdc_encryption_key_path(value: Path) -> Path:
    if not value.name.endswith(f"{FileExtensions.KEY}{FileExtensions.GPG}"):
        raise ValidationError("Missing a valid encryption key.")
    return value


def validated_pdc_sequencing_file_path(value: Path) -> Path:
    if not value.name.endswith(f"{FileExtensions.TAR}{FileExtensions.GZIP}{FileExtensions.GPG}"):
        raise ValidationError("Missing a valid sequence file.")
    return value
