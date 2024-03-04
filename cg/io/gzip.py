import gzip
from pathlib import Path


def read_gzip_first_line(file_path: Path) -> str:
    """Return first line of gzip file."""
    with gzip.open(file_path) as file:
        return file.readline().decode()
