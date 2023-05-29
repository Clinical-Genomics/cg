from pathlib import Path
from typing import Any
from requests import Response

from cg.constants.constants import FileFormat, APIMethods
from cg.io.json import read_json, write_json, write_json_stream, read_json_stream
from cg.io.yaml import read_yaml, write_yaml, read_yaml_stream, write_yaml_stream
from cg.io.csv import read_csv, write_csv, read_csv_stream, write_csv_stream
from cg.io.xml import read_xml, write_xml
from cg.io.api import put, post, patch, delete, get


class ReadFile:
    """Reading file using different methods."""

    read_file = {
        FileFormat.CSV: read_csv,
        FileFormat.JSON: read_json,
        FileFormat.YAML: read_yaml,
        FileFormat.XML: read_xml,
    }

    @classmethod
    def get_content_from_file(cls, file_format: str, file_path: Path, **kwargs) -> Any:
        """Read file using file format dispatch table."""
        return cls.read_file[file_format](file_path=file_path, **kwargs)


class ReadStream:
    """Reading stream using different methods."""

    read_stream = {
        FileFormat.CSV: read_csv_stream,
        FileFormat.JSON: read_json_stream,
        FileFormat.YAML: read_yaml_stream,
    }

    @classmethod
    def get_content_from_stream(cls, file_format: str, stream: Any) -> Any:
        """Read stream using file format dispatch table."""
        return cls.read_stream[file_format](stream=stream)


class WriteFile:
    """Write file using different methods."""

    write_file = {
        FileFormat.CSV: write_csv,
        FileFormat.JSON: write_json,
        FileFormat.YAML: write_yaml,
        FileFormat.XML: write_xml,
    }

    @classmethod
    def write_file_from_content(cls, content: Any, file_format: str, file_path: Path) -> None:
        """Write file using file format dispatch table."""
        cls.write_file[file_format](content=content, file_path=file_path)


class WriteStream:
    """Write stream using different methods."""

    write_stream = {
        FileFormat.CSV: write_csv_stream,
        FileFormat.JSON: write_json_stream,
        FileFormat.YAML: write_yaml_stream,
    }

    @classmethod
    def write_stream_from_content(cls, content: Any, file_format: str) -> str:
        """Write stream using file format dispatch table."""
        return cls.write_stream[file_format](content=content)


class APIRequest:
    """Create API requests."""

    api_request = {
        APIMethods.PUT: put,
        APIMethods.POST: post,
        APIMethods.DELETE: delete,
        APIMethods.PATCH: patch,
        APIMethods.GET: get,
    }

    @classmethod
    def api_request_from_content(
        cls, api_method: str, url: str, headers: dict, json: dict
    ) -> Response:
        return cls.api_request[api_method](url=url, headers=headers, json=json)
