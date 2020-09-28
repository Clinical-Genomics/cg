"""
This module handles concatenation of usalt fastq files.

Classes:
    FastqFileNameCreator: Creates valid usalt filenames
    FastqHandler: Handles fastq file linking
"""
import logging
from typing import List

LOGGER = logging.getLogger(__name__)


class BaseFastqHandler:
    """Handles fastq file linking"""

    class BaseFastqFileNameCreator:
        """Creates valid usalt filename from the parameters"""

        @staticmethod
        def create(lane: str, flowcell: str, sample: str, read: str, more: dict = None) -> str:
            """Name a FASTQ file following pipeline conventions."""

    def __init__(self, config):
        pass

    def link(self, case: str, sample: str, files: List[dict]):
        """Link FASTQ files for a pipeline sample."""
