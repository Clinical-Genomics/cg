"""Delivery report template utility functions."""

import base64
from pathlib import Path


def get_base64_from_png(png_path: Path) -> str:
    """Return base64 encoding of a PNG image."""
    with open(png_path, "rb") as png_file:
        encoded_string: str = base64.b64encode(png_file.read()).decode("utf-8")
    return f"data:image/png;base64,{encoded_string}"
