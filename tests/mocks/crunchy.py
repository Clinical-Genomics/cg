"""Mock the crunchy API"""

import logging
from pathlib import Path

from cg.apps.crunchy.crunchy import CrunchyAPI

LOG = logging.getLogger(__name__)


class MockCrunchyAPI(CrunchyAPI):
    """
        Mock for the crunchy API
    """

    def __init__(self, config: dict = None):

        self.config = config
        self.dry_run = False
        self._cram_compression_pending = {}
        self._bam_compression_possible = {}
        self._bam_compression_done = {}
        self._bam_compression_done_all = False

        self._spring_compression_pending = False
        self._spring_compression_possible = True
        self._spring_compression_done = False

        self._nr_fastq_compressions = 0

    def set_dry_run(self, dry_run: bool):
        """Update dry run"""
        self.dry_run = dry_run

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
        """Set if spring compression should be in pending state"""
        self._spring_compression_pending = True

    def set_spring_compression_done(self):
        """Set if spring compression should be in done state"""
        self._spring_compression_done = True

    def nr_fastq_compressions(self):
        """Return the number of times that fastq compression was called"""
        return self._nr_fastq_compressions

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
        self._nr_fastq_compressions += 1
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
        return self._spring_compression_pending
