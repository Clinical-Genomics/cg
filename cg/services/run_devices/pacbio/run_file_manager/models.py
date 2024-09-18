from pathlib import Path

from pydantic import BaseModel


class PacBioRunValidatorFiles(BaseModel):
    manifest_file: Path
    decompression_target: Path | None
    decompression_destination: Path
