"""Class to hold information about file objects"""

import gzip
import logging
from pathlib import Path
from typing import Iterable

GZIP_MAGIC_NUMBER = "1f8b"

LOG = logging.getLogger(__name__)


class FileData:
    """Helper functions for working with files"""

    @staticmethod
    def is_gzipped(path: Path) -> bool:
        """Check if file is zipped"""
        LOG.info("Check if file %s is gzipped", path)
        handle = open(path, "rb")
        if handle.read(2).hex() == GZIP_MAGIC_NUMBER:
            LOG.info("File %s is gzipped!", path)
            return True
        LOG.info("File %s is not gzipped!", path)
        return False

    @staticmethod
    def is_empty(path: Path) -> bool:
        """Check if file is empty"""
        LOG.info("Check if file %s is empty", path)
        if FileData.is_gzipped(path):
            return FileData.is_gzipped_empty(path)

        size = path.stat().st_size
        if size == 0:
            LOG.info("File %s is empty!", path)
            return True
        LOG.info("File %s is not empty", path)
        return False

    @staticmethod
    def get_file_content(path: Path) -> str:
        """Read the content of a file and return it"""
        handle = FileData.get_file_handle(path)
        return handle.read()

    @staticmethod
    def is_gzipped_empty(path: Path) -> bool:
        """Check if gzipped file is empty

        To make sure that the file is really empty we read small files to check if there are
        any content.
        If the file has more content that just metadata it is not empty.
        """
        size = path.stat().st_size
        if size > 100:
            LOG.info("File %s is not empty", path)
            return False

        content = FileData.get_file_content(path)

        if content:
            LOG.info("File %s is not empty", path)
            return False
        LOG.info("File %s is empty", path)
        return True

    @staticmethod
    def get_file_handle(path: Path) -> Iterable[str]:
        """Return the file handle of a path"""
        if FileData.is_gzipped(path):
            return gzip.open(path, "r")
        return open(path, "r")
