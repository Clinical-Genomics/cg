"""Module to read or write config files"""
from pathlib import Path
from typing import Any


def read_config(file_path: Path) -> Any:
    """Read content in a config file"""
    with open(file_path, "r") as file:
        return file.read()


def write_config(content: Any, file_path: Path) -> None:
    """Write content to a config file"""
    with open(file_path, "w") as file:
        file.write(content)


def concat_configs(file_paths: list[Path], target_file: Path, str_content: str = "") -> None:
    """Concatenate config files and string content"""
    content = str_content
    for file_path in file_paths:
        content = content + read_config(file_path)
    write_config(content, target_file)


def write_config_nextflow_style(content: dict[str, Any]) -> str:
    """Write content to stream accepted by Nextflow config files with non-quoted booleans and quoted strings."""
    for key, value in content.items():
        if isinstance(value, Path):
            value: str = value.as_posix()
        quotes = '"' if type(value) is str else ""
        return f"params.{key} = {quotes}{value}{quotes}\n"
