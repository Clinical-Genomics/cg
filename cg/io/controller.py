from pathlib import Path
from typing import Any

from requests import Response

from cg.constants.constants import APIMethods, FileFormat
from cg.io.api import delete, get, patch, post, put
from cg.io.csv import read_csv, read_csv_stream, write_csv, write_csv_stream
from cg.io.json import read_json, read_json_stream, write_json, write_json_stream
from cg.io.png import read_png
from cg.io.txt import read_txt, write_txt
from cg.io.xml import read_xml, write_xml
from cg.io.yaml import read_yaml, read_yaml_stream, write_yaml, write_yaml_stream


class ReadFile:
    """Reading file using different methods."""

    read_file = {
        FileFormat.CSV: read_csv,
        FileFormat.JSON: read_json,
        FileFormat.YAML: read_yaml,
        FileFormat.XML: read_xml,
        FileFormat.TXT: read_txt,
        FileFormat.PNG: read_png,
    }

    @classmethod
    def get_content_from_file(cls, file_format: str, file_path: Path, **kwargs: object) -> Any:
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
        FileFormat.TXT: write_txt,
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
        cls, api_method: str, url: str, headers: dict, json: dict, verify: bool = True
    ) -> Response:
        return cls.api_request[api_method](url=url, headers=headers, json=json, verify=verify)
