"""Module to read or write yaml files"""
from pathlib import Path
from typing import Union

import yaml


def read_yaml(file_path: Path) -> Union[dict, list]:
    """Read a yaml into dict"""
    with open(file_path, "r") as file:
        return yaml.safe_load(file)


def read_yaml_stream(stream: str) -> Union[dict, list]:
    "Read yaml formatted stream"
    return yaml.safe_load(stream)


def write_yaml(content: Union[dict, list], file_path: Path) -> None:
    """Write content to a yaml file"""
    with open(file_path, "w") as file:
        yaml.dump(content, file, explicit_start=True)


def write_yaml_stream(content: Union[dict, list]) -> str:
    """Write content to a yaml stream"""
    return yaml.dump(content)


def is_valid_yaml_file(file_path: Path) -> bool:
    """Returns true if the file was successfully loaded as yaml"""
    try:
        read_yaml(file_path=file_path)
    except yaml.YAMLError:
        return False
    return True
