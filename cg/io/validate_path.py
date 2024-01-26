"""Module to validate paths."""

import logging
from pathlib import Path

from cg.exc import ValidationError

LOG = logging.getLogger(__name__)


def validate_file_suffix(path_to_validate: Path, target_suffix: str) -> bool:
    """Validate file suffix of supplied path."""
    if path_to_validate.suffix != target_suffix:
        LOG.warning(f"File in path {path_to_validate} seems to be in wrong format")
        LOG.warning(f"Suffix {path_to_validate.suffix} is not {target_suffix}")
        raise ValidationError("Incorrect suffix")
    return True
