"""Fixtures for the PacBio post processing services."""

from pathlib import Path

import pytest

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.services.post_processing.pacbio.housekeeper_service.pacbio_houskeeper_service import (
    PacBioHousekeeperService,
)
from cg.services.post_processing.pacbio.metrics_parser.metrics_parser import PacBioMetricsParser
from cg.services.post_processing.pacbio.metrics_parser.models import PacBioMetrics
from cg.services.post_processing.pacbio.run_data_generator.run_data import PacBioRunData
from cg.services.post_processing.pacbio.run_file_manager.run_file_manager import (
    PacBioRunFileManager,
)


@pytest.fixture
def expected_pac_bio_run_data(
    pac_bio_test_run_name: str, pac_bio_smrt_cell_dir_1_a01: Path
) -> PacBioRunData:
    return PacBioRunData(
        full_path=pac_bio_smrt_cell_dir_1_a01,
        sequencing_run_name=pac_bio_test_run_name,
        well_name="A01",
        plate="1",
    )
