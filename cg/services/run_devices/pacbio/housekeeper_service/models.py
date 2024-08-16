from pathlib import Path

from pydantic import BaseModel


class PacBioFileData(BaseModel):
    bundle_name: str
    file_path: Path
    tags: list[str]
