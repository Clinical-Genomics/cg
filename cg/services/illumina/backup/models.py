from datetime import datetime
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, BeforeValidator

from cg.services.illumina.backup.validators import (
    is_valid_dsmc_encryption_key_path,
    is_valid_dsmc_sequencing_file_path,
)


class DsmcEncryptionKey(BaseModel):
    """Model representing the response from a PDC query."""

    dateTime: datetime
    path: Annotated[Path, BeforeValidator(is_valid_dsmc_encryption_key_path)]


class DsmcSequencingFile(BaseModel):
    """Model representing the response from a PDC query."""

    dateTime: datetime
    path: Annotated[Path, BeforeValidator(is_valid_dsmc_sequencing_file_path)]
