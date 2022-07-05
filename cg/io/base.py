from pathlib import Path
from typing import Any

from cg.constants.constants import FileFormat
from cg.io.yaml import read_yaml


class ReadFile:
    """Reading files using different methods"""

    read_file = {
        FileFormat.YAML: read_yaml,
    }

    def get_dict_from_file(self, file_format: str, file_path: Path) -> Any:
        """Read file using file format dispatch table"""
        return self.read_file[file_format](file_path=file_path)
