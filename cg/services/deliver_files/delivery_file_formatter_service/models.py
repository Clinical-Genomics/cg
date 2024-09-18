from pathlib import Path
from pydantic import BaseModel


class FormattedFile(BaseModel):
    original_path: Path
    formatted_path: Path


class FormattedFiles(BaseModel):
    files: list[FormattedFile]
