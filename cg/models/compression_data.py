"""Class to hold file information about a compression entity"""
import logging
import os
from datetime import datetime
from pathlib import Path

from cg.constants import FASTQ_FIRST_READ_SUFFIX, FASTQ_SECOND_READ_SUFFIX, FileExtensions
from cg.constants.compression import PENDING_PATH_SUFFIX

LOG = logging.getLogger(__name__)


class CompressionData:
    """Holds information about compression data"""

    def __init__(self, stub: Path = None):
        """Initialise a compression data object

        The stub is first part of the file name
        """
        self.stub = stub
        self.stub_string = str(self.stub)

    @property
    def pending_path(self) -> Path:
        """Return the path to a compression pending file"""
        return self.stub.with_suffix(PENDING_PATH_SUFFIX)

    @property
    def spring_path(self) -> Path:
        """Return the path to a SPRING file"""
        return self.stub.with_suffix(FileExtensions.SPRING)

    @property
    def encrypted_spring_path(self) -> Path:
        """Return the path to a SPRING file"""
        return self.stub.with_suffix(FileExtensions.SPRING).with_suffix(FileExtensions.GPG)

    @property
    def spring_metadata_path(self) -> Path:
        """Return the path to a SPRING metadata file"""
        return self.stub.with_suffix(".json")

    @property
    def analysis_dir(self) -> Path:
        """Return the path to folder where analysis is"""
        return self.stub.resolve().parent

    @property
    def fastq_first(self) -> Path:
        """Return the path to the first read in pair"""
        return Path(self.stub_string + FASTQ_FIRST_READ_SUFFIX)

    @property
    def fastq_second(self) -> Path:
        """Return the path to the second read in pair"""
        return Path(self.stub_string + FASTQ_SECOND_READ_SUFFIX)

    @property
    def run_name(self) -> str:
        """Return the name of the sequencing run identifier"""
        return self.stub.name

    def pair_exists(self) -> bool:
        """Check that both files in FASTQ pair exists"""
        LOG.info("Check if FASTQ pair exists")
        if not self.file_exists_and_is_accesible(self.fastq_first):
            return False
        return bool(self.file_exists_and_is_accesible(self.fastq_second))

    @staticmethod
    def is_absolute(file_path: Path) -> bool:
        """Check if file path can be resolved"""
        if not file_path.is_absolute():
            LOG.info("Could not resolve full path from HK to %s", file_path)
            return False
        return True

    @staticmethod
    def file_exists_and_is_accesible(file_path: Path) -> bool:
        """Check if file exists and is accesible"""
        try:
            if not file_path.exists():
                LOG.info("%s does not exist", file_path)
                return False
        except PermissionError:
            LOG.warning("Not permitted to access %s. Skipping", file_path)
            return False
        return True

    @staticmethod
    def get_nlinks(file_path: Path) -> int:
        """Get number of links to path"""
        LOG.info("Check nr of links for %s", file_path)
        return os.stat(file_path).st_nlink

    @staticmethod
    def is_symlink(file_path: Path) -> bool:
        """Check if file path is symbolik link"""
        LOG.info("Check if %s is a symlink", file_path)
        return os.path.islink(file_path)

    @staticmethod
    def get_change_date(file_path: Path) -> datetime:
        """Return the time when this file was changed"""
        changed_date = datetime.fromtimestamp(file_path.stat().st_mtime)
        LOG.info("File %s was changed %s", file_path, changed_date)
        return changed_date

    def spring_exists(self) -> bool:
        """Check if the SPRING file exists"""
        LOG.info("Check if SPRING archive file exists")
        return self.file_exists_and_is_accesible(self.spring_path)

    def metadata_exists(self) -> bool:
        """Check if the SPRING metadata file exists"""
        LOG.info("Check if SPRING metadata file exists")
        return self.file_exists_and_is_accesible(self.spring_metadata_path)

    def pending_exists(self) -> bool:
        """Check if the SPRING pending flag file exists"""
        LOG.info("Check if pending compression file exists")
        return self.file_exists_and_is_accesible(self.pending_path)

    def __str__(self):
        return f"CompressionData(run:{self.run_name})"

    def __repr__(self):
        return f"CompressionData(stub:{self.stub})"
