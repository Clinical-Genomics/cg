"""Class to hold information about file objects"""

import gzip
from pathlib import Path
from typing import Iterable

GZIP_MAGIC_NUMBER = "1f8b"


class FileData:
    """Helper functions for working with files"""

    @staticmethod
    def is_gzipped(path: Path) -> bool:
        """Check if file is zipped"""
        handle = open(path, "rb")
        if handle.read(2).hex() == GZIP_MAGIC_NUMBER:
            return True
        return False

    @staticmethod
    def is_empty(path: Path) -> bool:
        """Check if file is empty"""
        handle = open(path, "rb")
        if handle.read(1):
            return False
        return True

    @staticmethod
    def get_file_handle(path: Path) -> Iterable[str]:
        """Return the file handle of a path"""
        if FileData.is_gzipped(path):
            return gzip.open(path, "r")
        return open(path, "r")
