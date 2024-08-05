"""Module to read PNG image files."""

import base64
from pathlib import Path

from cg.constants import FileExtensions
from cg.io.validate_path import validate_file_suffix


def read_png(file_path: Path) -> str:
    """Return base64 encoding of a PNG image."""
    validate_file_suffix(path_to_validate=file_path, target_suffix=FileExtensions.PNG)
    with open(file_path, "rb") as png_file:
        encoded_string: str = base64.b64encode(png_file.read()).decode("utf-8")
    return f"data:image/png;base64,{encoded_string}"
