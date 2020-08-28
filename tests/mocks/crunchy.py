"""Mock the crunchy API"""

import logging
from pathlib import Path

from cg.apps.crunchy.crunchy import CrunchyAPI
from cg.models import CompressionData

LOG = logging.getLogger(__name__)


class MockCrunchyAPI(CrunchyAPI):
    """
    Mock for the crunchy API
    """

    def __init__(self, config: dict = None):

        self.config = config
        self.dry_run = False
        self._compression_pending_files = {}
        self._compression_possible_files = {}

        self._compression_pending = False
        self._compression_possible = True
        self._compression_done_all = False
        self._spring_compression_done = False

        self._nr_fastq_compressions = 0

    def set_dry_run(self, dry_run: bool):
        """Update dry run"""
        self.dry_run = dry_run

    # Mock specific methods
    def set_compression_pending(self, file_path: Path):
        """Set that the compression for a file is pending"""
        self._compression_pending_files[file_path] = True

    def set_compression_pending_all(
        self,
    ):
        """Set that the compression for a file is pending"""
        self._compression_pending = True

    def set_compression_not_possible(self, file_path: Path):
        """Set the variable so that bam/cram compression is not possible"""
        print("Setting compression to not possible for %s" % file_path)
        self._compression_possible_files[file_path] = False

    def set_spring_compression_done(self):
        """Set if spring compression should be in done state"""
        self._compression_done_all = True

    def nr_fastq_compressions(self):
        """Return the number of times that fastq compression was called"""
        return self._nr_fastq_compressions

    # Mocked methods
    def fastq_to_spring(self, compression_obj: CompressionData, sample_id: str = ""):
        """
        Compress FASTQ files into SPRING by sending to sbatch SLURM
        """
        self._nr_fastq_compressions += 1
        self.set_compression_pending_all()

    def spring_to_fastq(self, compression_obj: CompressionData, sample_id: str = ""):
        """Mock method that compress spring to fastq"""
        self._nr_fastq_compressions += 1
        self.set_compression_pending_all()

    def update_metadata_date(self, spring_metadata_path):
        print(f"Updates {spring_metadata_path}")

    def is_fastq_compression_possible(self, compression_obj: CompressionData) -> bool:
        """Check if it compression/decompression is possible"""
        if self._compression_pending:
            print("Compression pending")
            return False

        if self._compression_pending_files.get(compression_obj.fastq_first):
            print(f"Compression pending for file {compression_obj.fastq_first}")
            return False

        if self._compression_done_all:
            print(f"Compression done")
            return False

        compression_possible = self._compression_possible_files.get(
            compression_obj.fastq_first, self._compression_possible
        )
        print(f"Compression possible {compression_possible}")
        return compression_possible

    def is_fastq_compression_done(self, compression_obj: CompressionData) -> bool:
        """Check if spring compression if finished"""
        return self._compression_done_all

    def is_compression_pending(self, compression_obj: CompressionData) -> bool:
        """Check if compression has started, but not yet finished"""
        return self._compression_pending
