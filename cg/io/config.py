"""Module to read or write config files"""

from pathlib import Path
from typing import Any

def write_config_nextflow_style(content: dict[str, Any]) -> str:
    """Write content to stream accepted by Nextflow config files with non-quoted booleans and quoted strings."""
    string = ""
    for key, value in content.items():
        if isinstance(value, Path):
            value: str = value.as_posix()
        quotes = '"' if type(value) is str else ""
        string += f"params.{key} = {quotes}{value}{quotes}\n"
    return string
