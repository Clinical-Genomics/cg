from pathlib import Path

from pydantic import BaseModel


class PacBioRunValidatorFiles(BaseModel):
    manifest_file: Path
    decompression_target: Path
    decompression_destination: Path
