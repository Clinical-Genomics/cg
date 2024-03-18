from pathlib import Path
from typing import Any
from cg.constants.symbols import EMPTY_STRING


def write_config_nextflow_style(content: dict[str, Any] | None) -> str:
    """Write content to stream accepted by Nextflow config files with non-quoted booleans and quoted strings."""
    string: str = EMPTY_STRING
    double_quotes: str = '"'
    for parameter, value in content.items():
        if isinstance(value, Path):
            value: str = value.as_posix()
        quotes = double_quotes if type(value) is str else EMPTY_STRING
        string += f"params.{parameter} = {quotes}{value}{quotes}\n"
    return string
