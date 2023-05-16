"""Module for reading and writing comma separated values (CSV) formatted files."""
import csv
import io
from typing import Any, List, Union
from pathlib import Path

from cg.constants import FileExtensions
from cg.io.validate_path import validate_file_suffix


def read_csv(file_path: Path, read_to_dict: bool = False) -> Union[List[List[str]], List[dict]]:
    """Read content in a CSV file to a list of list or list of dict."""
    validate_file_suffix(path_to_validate=file_path, target_suffix=FileExtensions.CSV)
    with open(file_path, "r") as file:
        csv_reader = csv.DictReader(file) if read_to_dict else csv.reader(file)
        return list(csv_reader)


def read_csv_stream(stream: str) -> List[List[str]]:
    """Read CSV formatted stream."""
    csv_reader = csv.reader(stream.splitlines())
    return list(csv_reader)


def write_csv(content: List[List[Any]], file_path: Path) -> None:
    """Write content to a CSV file."""
    with open(file_path, "w", newline="") as file:
        csv_writer = csv.writer(file)
        for row in content:
            csv_writer.writerow(row)


def write_csv_stream(content: List[List[Any]]) -> str:
    """Write content to a CSV stream."""
    csv_stream = io.StringIO()
    csv_writer = csv.writer(csv_stream, lineterminator="\n")
    for row in content:
        csv_writer.writerow(row)
    return csv_stream.getvalue()
