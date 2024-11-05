from datetime import datetime
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, BeforeValidator

from cg.services.illumina.backup.validators import (
    validated_pdc_encryption_key_path,
    validated_pdc_sequencing_file_path,
)


class PdcEncryptionKey(BaseModel):
    """Model representing the response from a PDC query."""

    date_time: datetime
    path: Annotated[Path, BeforeValidator(validated_pdc_encryption_key_path)]


class PdcSequencingFile(BaseModel):
    """Model representing the response from a PDC query."""

    date_time: datetime
    path: Annotated[Path, BeforeValidator(validated_pdc_sequencing_file_path)]
