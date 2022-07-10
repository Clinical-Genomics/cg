from pathlib import Path
from typing import Union

from cg.constants.constants import FileFormat
from cg.io.yaml import read_yaml, write_yaml, read_yaml_stream, write_yaml_stream


class ReadFile:
    """Reading file using different methods"""

    read_file = {
        FileFormat.YAML: read_yaml,
    }

    def get_content_from_file(self, file_format: str, file_path: Path) -> Union[dict, list]:
        """Read file using file format dispatch table"""
        return self.read_file[file_format](file_path=file_path)


class ReadStream:
    "Reading stream using different methods"
    read_stream = {
        FileFormat.YAML: read_yaml_stream,
    }

    def get_content_from_stream(
        self, file_format: str, stream: Union[dict, list]
    ) -> Union[dict, list]:
        """Read stream using file format dispatch table"""
        return self.read_stream[file_format](stream=stream)


class WriteFile:
    """write file using different methods"""

    write_file = {
        FileFormat.YAML: write_yaml,
    }

    def write_file_from_content(self, content: dict, file_format: str, file_path: Path) -> None:
        """write file using file format dispatch table"""
        self.write_file[file_format](content=content, file_path=file_path)
        return


class WriteStream:
    """write stream using different methods"""

    write_stream = {
        FileFormat.YAML: write_yaml_stream,
    }

    def write_stream_from_content(self, content: dict, file_format: str) -> str:
        """write stream using file format dispatch table"""
        return self.write_stream[file_format](content=content)
