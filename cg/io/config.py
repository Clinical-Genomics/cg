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

def concat_configs(file_paths: list[Path], target_file: Path) -> str:
    """Write content to a yaml stream"""
    content = ""
    for file_path in file_paths:
        content = content + read_config(file_path)
    write_config(content, target_file)


# def write_yaml_nextflow_style(content: dict[str, Any], file_path: Path) -> None:
#     """Write content to yaml file accepted by Nextflow with non-quoted booleans and quoted strings."""
#     with open(file_path, "w") as outfile:
#         for key, value in content.items():
#             if isinstance(value, Path):
#                 value: str = value.as_posix()
#             quotes = '"' if type(value) is str else ""
#             outfile.write(f"{key}: {quotes}{value}{quotes}\n")

