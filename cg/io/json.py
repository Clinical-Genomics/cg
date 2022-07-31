from pathlib import Path
from typing import Any

import json


def read_json(file_path: Path) -> Any:
    """Read content in a json file"""
    with open(file_path, "r") as file:
        return json.load(file)


def write_json(content: Any, file_path: Path) -> None:
    """Write content to a json file"""
    with open(file_path, "w") as file:
        json.dump(content, file)
