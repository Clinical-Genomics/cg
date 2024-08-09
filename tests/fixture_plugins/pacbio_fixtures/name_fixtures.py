"""Module for PacBio fixtures returning strings."""

import pytest

from cg.constants.pacbio import PacBioDirsAndFiles
from cg.services.post_processing.pacbio.metrics_parser.metrics_parser import PacBioMetricsParser
from cg.services.post_processing.pacbio.metrics_parser.models import PacBioMetrics


@pytest.fixture
def pac_bio_smrt_cell_name() -> str:
    return "1_A01"


@pytest.fixture
def pac_bio_test_run_name() -> str:
    """Return the name of a PacBio SMRT cell."""
    return "r84202_20240522_133539"


@pytest.fixture
def pac_bio_sequencing_run_name(pac_bio_test_run_name: str, pac_bio_smrt_cell_name: str) -> str:
    """Return the name of a PacBio SMRT cell."""
    return f"{pac_bio_test_run_name}/{pac_bio_smrt_cell_name})"


@pytest.fixture
def pac_bio_1_a01_cell_full_name() -> str:
    """Return the full name of a PacBio SMRT cell."""
    return "m84202_240522_135641_s1"


@pytest.fixture
def ccs_report_1_a01_name(pac_bio_1_a01_cell_full_name: str) -> str:
    """Return the name of a ccs report file."""
    return f"{pac_bio_1_a01_cell_full_name}.{PacBioDirsAndFiles.CCS_REPORT_SUFFIX}"


@pytest.fixture
def expected_smrt_cell_bundle_name(
    pac_bio_metrics_parser: PacBioMetricsParser, expected_pac_bio_run_data
) -> str:
    parsed_metrics: PacBioMetrics = pac_bio_metrics_parser.parse_metrics(expected_pac_bio_run_data)
    return parsed_metrics.dataset_metrics.cell_id


@pytest.fixture
def expected_pac_bio_sample_name(
    pac_bio_metrics_parser: PacBioMetricsParser, expected_pac_bio_run_data
):
    parsed_metrics: PacBioMetrics = pac_bio_metrics_parser.parse_metrics(expected_pac_bio_run_data)
    return parsed_metrics.dataset_metrics.sample_internal_id
