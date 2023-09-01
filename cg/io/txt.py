"""Module to read or write txt files."""

from pathlib import Path
from typing import List, Union


def read_txt(file_path: Path, read_to_string: bool = False) -> Union[List[str], str]:
    """Read content in a TXT file."""
    with open(file_path, "r") as file:
        if read_to_string:
            return file.read()
        return list(file)
