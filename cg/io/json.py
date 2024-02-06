import json
from pathlib import Path
from typing import Any


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
