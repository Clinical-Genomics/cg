"""Module to read or write yaml files"""
from pathlib import Path

import yaml


def read_yaml(file_path: Path) -> dict:
    """Read a yaml into dict"""
    with open(file_path, "r") as file:
        return yaml.safe_load(file)


def write_yaml(content: dict, file_path: Path) -> None:
    """Write a dict to a yaml file"""
    with open(file_path, "w") as file:
        return yaml.dump(content, file)
