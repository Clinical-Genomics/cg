import json
from pathlib import Path
from typing import Any
from cg.constants.symbols import EMPTY_STRING


def read_json(file_path: Path) -> Any:
    """Read content in a json file"""
    with open(file_path, "r") as file:
        return json.load(file)


def read_json_stream(stream: str) -> Any:
    """Read json formatted stream"""
    return json.loads(stream)


def write_json(content: Any, file_path: Path) -> None:
    """Write content to a json file"""
    with open(file_path, "w") as file:
        json.dump(content, file, indent=4)


def write_json_stream(content: Any) -> str:
    """Write content to a json stream"""
    return json.dumps(content)

def write_config_nextflow_style(content: dict[str, Any] | None) -> str:
    """Write content to stream accepted by Nextflow config files with non-quoted booleans and quoted strings."""
    string: str = EMPTY_STRING
    double_quotes: str = '"'
    for parameter, value in content.items():
        if isinstance(value, Path):
            value: str = value.as_posix()
        quotes = double_quotes if type(value) is str else EMPTY_STRING
        string += f"params.{parameter}: {quotes}{value}{quotes}\n"
    return string
