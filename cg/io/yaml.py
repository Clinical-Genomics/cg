"""Module to read or write yaml files"""
from pathlib import Path
from typing import Any

import yaml


def read_yaml(file_path: Path) -> Any:
    """Read content in a yaml file"""
    with open(file_path, "r") as file:
        return yaml.safe_load(file)


def read_yaml_stream(stream: str) -> Any:
    """Read yaml formatted stream"""
    return yaml.safe_load(stream)


def write_yaml(content: Any, file_path: Path) -> None:
    """Write content to a yaml file"""
    with open(file_path, "w") as file:
        yaml.dump(content, file, explicit_start=True)


def write_yaml_stream(content: Any) -> str:
    """Write content to a yaml stream"""
    return yaml.dump(content)
