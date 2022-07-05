"""Module to read or write yaml files"""
from pathlib import Path

import yaml


def read_yaml(file_path: Path) -> dict:
    """Read a yaml into dict"""
    with open(file_path, "r") as file:
        return yaml.safe_load(file)
