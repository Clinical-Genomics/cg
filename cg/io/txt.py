"""Module to read or write txt files."""

from pathlib import Path
from typing import Any


def read_txt(file_path: Path, read_to_string: bool = False) -> list[str] | str:
    """Read content in a TXT file."""
    with open(file_path, "r") as file:
        if read_to_string:
            return file.read()
        return list(file)


def write_txt(content: list[str] | str, file_path: Path) -> None:
    """Write content to a text file."""
    with open(file_path, "w") as file:
        if isinstance(content, list):
            file.writelines(content)
        else:
            file.write(content)
