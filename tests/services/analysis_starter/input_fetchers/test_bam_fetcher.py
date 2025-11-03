from unittest.mock import create_autospec

from cg.services.analysis_starter.input_fetcher.implementations.bam_fetcher import BamFetcher
from cg.store.store import Store


def test_ensure_files_are_ready_success():
    # GIVEN a case with all BAM files on disk

    # GIVEN a BamFetcher
    bam_fetcher = BamFetcher(status_db=create_autospec(Store))

    # WHEN ensuring that all files are ready
    # THEN no error is raised
    # THEN no error is raised
