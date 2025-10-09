"""Class to hold file information about a compression entity"""

import logging
import os
from datetime import date, datetime
from pathlib import Path

from cg.apps.crunchy.files import check_if_update_spring, get_crunchy_metadata, get_file_updated_at
from cg.apps.crunchy.models import CrunchyMetadata
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
        if not self.file_exists_and_is_accessible(self.fastq_first):
            return False
        return bool(self.file_exists_and_is_accessible(self.fastq_second))

    @staticmethod
    def is_absolute(file_path: Path) -> bool:
        """Check if file path can be resolved"""
        if not file_path.is_absolute():
            LOG.info("Could not resolve full path from HK to %s", file_path)
            return False
        return True

    @staticmethod
    def file_exists_and_is_accessible(file_path: Path) -> bool:
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
        return self.file_exists_and_is_accessible(self.spring_path)

    def metadata_exists(self) -> bool:
        """Check if the SPRING metadata file exists"""
        LOG.info("Check if SPRING metadata file exists")
        return self.file_exists_and_is_accessible(self.spring_metadata_path)

    def pending_exists(self) -> bool:
        """Check if the SPRING pending flag file exists"""
        LOG.info("Check if pending compression file exists")
        return self.file_exists_and_is_accessible(self.pending_path)

    @property
    def is_compression_pending(self) -> bool:
        """Check if compression/decompression has started but not finished."""
        if self.pending_exists():
            LOG.info(f"Compression/decompression is pending for {self.run_name}")
            return True
        LOG.info("Compression/decompression is not running")
        return False

    @property
    def is_fastq_compression_possible(self) -> bool:
        """Check if FASTQ compression is possible.

        - Compression is running          -> Compression NOT possible
        - SPRING file exists on Hasta     -> Compression NOT possible
        - Data is external                -> Compression NOT possible
        - Not compressed and not running  -> Compression IS possible
        """
        if self.is_compression_pending:
            return False

        if self.spring_exists():
            LOG.debug("SPRING file found")
            return False

        if "external-data" in str(self.fastq_first):
            LOG.debug("File is external data and should not be compressed")
            return False

        LOG.debug("FASTQ compression is possible")

        return True

    @property
    def is_spring_decompression_possible(self) -> bool:
        """Check if SPRING decompression is possible.

        There are three possible answers to this question:

            - Compression/Decompression is running      -> Decompression is NOT possible
            - The FASTQ files are not compressed        -> Decompression is NOT possible
            - Compression has been performed            -> Decompression IS possible

        """
        if self.pending_exists():
            LOG.info(f"Compression/decompression is pending for {self.run_name}")
            return False

        if not self.spring_exists():
            LOG.info("No SPRING file found")
            return False

        if self.pair_exists():
            LOG.info("FASTQ files already exists")
            return False

        LOG.info("Decompression is possible")

        return True

    @property
    def is_fastq_compression_done(self) -> bool:
        """Check if FASTQ compression is finished.

        This is checked by controlling that the SPRING files that are produced after FASTQ
        compression exists.

        The following has to be fulfilled for FASTQ compression to be considered done:

            - A SPRING archive file exists
            - A SPRING archive metadata file exists
            - The SPRING archive has not been unpacked before FASTQ delta (21 days)

        Note:
        'updated_at' indicates at what date the SPRING archive was unarchived last.
        If the SPRING archive has never been unarchived 'updated_at' is None.

        """
        LOG.info("Check if FASTQ compression is finished")
        LOG.info(f"Check if SPRING file {self.spring_path} exists")
        if not self.spring_exists():
            LOG.info(
                f"No SPRING file for {self.run_name}",
            )
            return False
        LOG.info("SPRING file found")

        LOG.info(f"Check if SPRING metadata file {self.spring_metadata_path} exists")
        if not self.metadata_exists():
            LOG.info("No metadata file found")
            return False
        LOG.info("SPRING metadata file found")

        # We want this to raise exception if file is malformed
        crunchy_metadata: CrunchyMetadata = get_crunchy_metadata(self.spring_metadata_path)

        # Check if the SPRING archive has been unarchived
        updated_at: date | None = get_file_updated_at(crunchy_metadata)
        if updated_at is None:
            LOG.info(f"FASTQ compression is done for {self.run_name}")
            return True

        LOG.info(f"Files where unpacked {updated_at}")

        if not check_if_update_spring(updated_at):
            return False

        LOG.info(f"FASTQ compression is done for {self.run_name}")

        return True

    @property
    def is_spring_decompression_done(self) -> bool:
        """Check if SPRING decompression if finished.

        This means that all three files specified in SPRING metadata should exist.
        That is

            - First read in FASTQ pair should exist
            - Second read in FASTQ pair should exist
            - SPRING archive file should still exist
        """

        spring_metadata_path: Path = self.spring_metadata_path
        LOG.info(f"Check if SPRING metadata file {spring_metadata_path} exists")

        if not self.metadata_exists():
            LOG.info("No SPRING metadata file found")
            return False

        # We want this to exit hard if the metadata is malformed
        crunchy_metadata: CrunchyMetadata = get_crunchy_metadata(spring_metadata_path)

        for file_info in crunchy_metadata.files:
            if not Path(file_info.path).exists():
                LOG.info(f"File {file_info.path} does not exist")
                return False
            if not file_info.updated:
                LOG.info("Files have not been unarchived")
                return False

        LOG.info(f"SPRING decompression is done for run {self.run_name}")
        return True

    def __str__(self):
        return f"CompressionData(run:{self.run_name})"

    def __repr__(self):
        return f"CompressionData(stub:{self.stub})"


class SampleCompressionData:
    """Object encapsulating a sample's compression status."""

    def __init__(self, sample_id: str, compression_objects: list[CompressionData]):
        self.sample_id = sample_id
        self.compression_objects = compression_objects

    def is_decompression_needed(self) -> bool:
        """Check if decompression is needed for the specified sample."""
        LOG.debug(f"Checking if decompression is needed for {self.sample_id}.")
        return any(
            not compression_object.is_compression_pending and not compression_object.pair_exists()
            for compression_object in self.compression_objects
        )

    def is_spring_decompression_running(self) -> bool:
        """Check if sample is being decompressed"""
        return any(
            compression_object.is_compression_pending
            for compression_object in self.compression_objects
        )

    def can_be_decompressed(self) -> bool:
        """Returns True if at least one Spring file can be decompressed, otherwise False"""
        return any(
            compression_object.is_spring_decompression_possible
            for compression_object in self.compression_objects
        )


class CaseCompressionData:
    """Object encapsulating a case's compression status."""

    def __init__(self, case_id: str, sample_compression_data: list[SampleCompressionData]):
        self.case_id = case_id
        self.sample_compression_data = sample_compression_data

    def is_spring_decompression_needed(self) -> bool:
        """Check if spring decompression needs to be started"""
        return any(
            sample_compression.is_decompression_needed()
            for sample_compression in self.sample_compression_data
        )

    def is_spring_decompression_running(self) -> bool:
        """Check if case is being decompressed"""
        return any(
            sample_compression.is_spring_decompression_running()
            for sample_compression in self.sample_compression_data
        )

    def can_at_least_one_sample_be_decompressed(self) -> bool:
        """Returns True if at least one sample can be decompressed, otherwise False"""
        return any(
            sample_compression.can_be_decompressed()
            for sample_compression in self.sample_compression_data
        )
