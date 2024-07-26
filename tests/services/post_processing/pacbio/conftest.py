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


@pytest.fixture
def pac_bio_run_file_manager() -> PacBioRunFileManager:
    return PacBioRunFileManager()


@pytest.fixture
def pac_bio_metrics_parser(pac_bio_run_file_manager: PacBioRunFileManager) -> PacBioMetricsParser:
    return PacBioMetricsParser(file_manager=pac_bio_run_file_manager)


@pytest.fixture
def pac_bio_housekeeper_service(
    real_housekeeper_api: HousekeeperAPI,
    pac_bio_run_file_manager: PacBioRunFileManager,
    pac_bio_metrics_parser: PacBioMetricsParser,
) -> PacBioHousekeeperService:
    return PacBioHousekeeperService(
        hk_api=real_housekeeper_api,
        file_manager=pac_bio_run_file_manager,
        metrics_parser=pac_bio_metrics_parser,
    )


@pytest.fixture
def expected_smrt_cell_bundle_name(
    pac_bio_metrics_parser: PacBioMetricsParser, expected_pac_bio_run_data
) -> str:
    parsed_metrics: PacBioMetrics = pac_bio_metrics_parser.parse_metrics(expected_pac_bio_run_data)
    return parsed_metrics.dataset_metrics.cell_id


@pytest.fixture
def expexted_pac_bio_sample_name(
    pac_bio_metrics_parser: PacBioMetricsParser, expected_pac_bio_run_data
):
    parsed_metrics: PacBioMetrics = pac_bio_metrics_parser.parse_metrics(expected_pac_bio_run_data)
    return parsed_metrics.dataset_metrics.sample_internal_id
