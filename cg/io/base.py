from pathlib import Path

from cg.constants.constants import FileFormat
from cg.io.yaml import read_yaml, write_yaml


class ReadFile:
    """Reading files using different methods"""

    read_file = {
        FileFormat.YAML: read_yaml,
    }

    def get_dict_from_file(self, file_format: str, file_path: Path) -> dict:
        """Read file using file format dispatch table"""
        return self.read_file[file_format](file_path=file_path)


class WriteFile:
    """write files using different methods"""

    write_file = {
        FileFormat.YAML: write_yaml,
    }

    def write_file_from_dict(self, content: dict, file_format: str, file_path: Path) -> dict:
        """write file using file format dispatch table"""
        return self.write_file[file_format](content=content, file_path=file_path)
