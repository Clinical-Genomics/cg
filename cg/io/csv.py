"""Module for reading and writing csv files."""
import csv
import io
from typing import Any, List, Tuple
from pathlib import Path


def read_csv(file_path: Path) -> List[List[str]]:
    """Read content in a csv file"""
    with open(file_path, "r") as file:
        csv_reader = csv.reader(file)
        return [row for row in csv_reader]


def read_csv_stream(stream: str) -> List[List[str]]:
    """Read csv formatted stream"""
    csv_reader = csv.reader(stream.splitlines())
    return [row for row in csv_reader]


def write_csv(content: List[List[Any]], file_path: Path) -> None:
    """Write content to a csv file"""
    with open(file_path, "w", newline="") as file:
        csv_writer = csv.writer(file)
        for row in content:
            csv_writer.writerow(row)


def write_csv_stream(content: List[List[Any]]) -> str:
    """Write content to a csv stream"""
    csv_stream = io.StringIO()
    csv_writer = csv.writer(csv_stream, lineterminator="\n")
    for row in content:
        csv_writer.writerow(row)
    return csv_stream.getvalue()
