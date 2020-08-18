"""Class to hold file information about a compression entity"""

from pathlib import Path

from cg.constants import (FASTQ_FIRST_READ_SUFFIX, FASTQ_SECOND_READ_SUFFIX,
                          HK_FASTQ_TAGS)

LOG = logging.getLogger(__name__)


class CompressionData:
    """Holds information about compression data"""

    def __init__(self, springh: Path = None, fastq: Path = None):
        """Initialise a compression data object"""
        self.spring = spring_path
        self.fastq = fastq

    @property
    def spring_path(self):
        """Return the path to a spring file"""
        pass

    @property
    def spring_metadata_path(self):
        """Return the path to a spring metadata file"""
        pass

    @property
    def fastq_first(self):
        """Return the path to the first read in pair"""
        pass

    @property
    def fastq_second(self):
        """Return the path to the second read in pair"""
        pass
