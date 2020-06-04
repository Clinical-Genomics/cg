"""Mock the crunchy API"""

import logging
from pathlib import Path

from cg.constants import (
    BAM_INDEX_SUFFIX,
    BAM_SUFFIX,
    CRAM_INDEX_SUFFIX,
    CRAM_SUFFIX,
    FASTQ_FIRST_READ_SUFFIX,
    FASTQ_SECOND_READ_SUFFIX,
    SPRING_SUFFIX,
)

FLAG_PATH_SUFFIX = ".crunchy.txt"
PENDING_PATH_SUFFIX = ".crunchy.pending.txt"

LOG = logging.getLogger(__name__)


class MockCrunchyAPI:
    """
        Mock for the crunchy API
    """

    def __init__(self, config: dict = None):

        self.config = config
        self._cram_compression_pending = {}
        self._bam_compression_possible = {}
        self._bam_compression_done = {}
        self._bam_compression_done_all = False

        self._spring_compression_pending = False
        self._spring_compression_possible = True
        self._spring_compression_done = False

    # Mock specific methods
    def set_cram_compression_pending(self, bam_path):
        """Set that the cram compression for a file is pending"""
        self._cram_compression_pending[bam_path] = True

    def set_bam_compression_done(self, bam_path):
        """Set the variable so that bam/cram compression is done"""
        self._bam_compression_done[bam_path] = True

    def set_bam_compression_done_all(self):
        """Set so that bam compression is done for all"""
        self._bam_compression_done_all = True

    def set_bam_compression_not_possible(self, bam_path):
        """Set the variable so that bam/cram compression is not possible"""
        print("Setting bam compression to not possible for %s", bam_path)
        self._bam_compression_possible[bam_path] = False

    def set_spring_compression_pending(self):
        """Create a pending path"""
        self._spring_compression_pending = True

    # Mocked methods
    def bam_to_cram(self, bam_path: Path, ntasks: int, mem: int, dry_run: bool = False):
        """
            Compress BAM file into CRAM
        """
        self._cram_compression_pending[bam_path] = True

    def fastq_to_spring(
        self, fastq_first: Path, fastq_second: Path, ntasks: int, mem: int, dry_run: bool = False,
    ):
        """
            Compress FASTQ files into SPRING by sending to sbatch SLURM
        """
        self.set_spring_compression_pending()

    def is_cram_compression_done(self, bam_path: Path) -> bool:
        """Check if CRAM compression already done for BAM file"""
        if self._bam_compression_done_all:
            return True

        return self._bam_compression_done.get(bam_path, False)

    def is_cram_compression_pending(self, bam_path: Path) -> bool:
        """Check if cram compression has started, but not yet finished"""
        return self._cram_compression_pending.get(bam_path, False)

    def is_bam_compression_possible(self, bam_path: Path) -> bool:
        """Check if it CRAM compression for BAM file is possible"""
        return self._bam_compression_possible.get(bam_path, True)

    def is_spring_compression_done(self, fastq_first: Path, fastq_second: Path) -> bool:
        """Check if spring compression if finished"""
        return self._spring_compression_done

    def is_spring_compression_pending(self, fastq: Path) -> bool:
        """Check if spring compression has started, but not yet finished"""
        return self._spring_compression_done

    @staticmethod
    def get_flag_path(file_path):
        """Get path to 'finished' flag.
        When compressing fastq this means that a .json metadata file has been created
        Otherwise, for bam compression, a regular flag path is returned.
        """
        if file_path.suffix == ".spring":
            return file_path.with_suffix("").with_suffix(".json")

        return file_path.with_suffix(FLAG_PATH_SUFFIX)

    @staticmethod
    def get_pending_path(file_path: Path) -> Path:
        """Gives path to pending-flag path

        There are two cases, either fastq or bam. They are treated as shown below
        """
        if str(file_path).endswith(FASTQ_FIRST_READ_SUFFIX):
            return Path(str(file_path).replace(FASTQ_FIRST_READ_SUFFIX, PENDING_PATH_SUFFIX))
        if str(file_path).endswith(FASTQ_SECOND_READ_SUFFIX):
            return Path(str(file_path).replace(FASTQ_SECOND_READ_SUFFIX, PENDING_PATH_SUFFIX))
        return file_path.with_suffix(PENDING_PATH_SUFFIX)

    @staticmethod
    def get_index_path(file_path: Path) -> dict:
        """Get possible paths for index

        Returns:
            dict: path with single_suffix, e.g. .bai and path with double_suffix, e.g. .bam.bai
        """
        index_type = CRAM_INDEX_SUFFIX
        if file_path.suffix == BAM_SUFFIX:
            index_type = BAM_INDEX_SUFFIX
        with_single_suffix = file_path.with_suffix(index_type)
        with_double_suffix = file_path.with_suffix(file_path.suffix + index_type)
        return {
            "single_suffix": with_single_suffix,
            "double_suffix": with_double_suffix,
        }

    @staticmethod
    def get_cram_path_from_bam(bam_path: Path) -> Path:
        """ Get corresponding CRAM file path from bam file path """
        if not bam_path.suffix == BAM_SUFFIX:
            LOG.error("%s does not end with %s", bam_path, BAM_SUFFIX)
            raise ValueError
        cram_path = bam_path.with_suffix(CRAM_SUFFIX)
        return cram_path

    @staticmethod
    def get_spring_path_from_fastq(fastq: Path) -> Path:
        """ GET corresponding SPRING file path from a FASTQ file"""
        suffix = FASTQ_FIRST_READ_SUFFIX
        if FASTQ_SECOND_READ_SUFFIX in str(fastq):
            suffix = FASTQ_SECOND_READ_SUFFIX

        spring_path = Path(str(fastq).replace(suffix, "")).with_suffix(SPRING_SUFFIX)
        return spring_path
