"""Module for PacBio fixtures returning service objects."""

import pytest

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.services.post_processing.pacbio.housekeeper_service.pacbio_houskeeper_service import (
    PacBioHousekeeperService,
)
from cg.services.post_processing.pacbio.metrics_parser.metrics_parser import PacBioMetricsParser
from cg.services.post_processing.pacbio.run_file_manager.run_file_manager import (
    PacBioRunFileManager,
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
