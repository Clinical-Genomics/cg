"""Module for PacBio fixtures returning service objects."""

from pathlib import Path
from unittest.mock import Mock

import pytest

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.services.run_devices.pacbio.data_storage_service.pacbio_store_service import (
    PacBioStoreService,
)
from cg.services.run_devices.pacbio.data_transfer_service.data_transfer_service import (
    PacBioDataTransferService,
)
from cg.services.run_devices.pacbio.housekeeper_service.pacbio_houskeeper_service import (
    PacBioHousekeeperService,
)
from cg.services.run_devices.pacbio.metrics_parser.metrics_parser import PacBioMetricsParser
from cg.services.run_devices.pacbio.post_processing_service import PacBioPostProcessingService
from cg.services.run_devices.pacbio.run_data_generator.pacbio_run_data_generator import (
    PacBioRunDataGenerator,
)
from cg.services.run_devices.pacbio.run_file_manager.run_file_manager import PacBioRunFileManager
from cg.services.run_devices.pacbio.run_validator.pacbio_run_validator import PacBioRunValidator
from cg.services.run_devices.run_names.pacbio import PacbioRunNamesService
from cg.store.store import Store

# Mocked services


@pytest.fixture
def mock_pacbio_run_validator() -> PacBioRunValidator:
    return PacBioRunValidator(
        decompressor=Mock(),
        file_transfer_validator=Mock(),
        file_manager=Mock(),
    )


# Real services


@pytest.fixture
def pac_bio_run_data_generator() -> PacBioRunDataGenerator:
    return PacBioRunDataGenerator()


@pytest.fixture
def pac_bio_run_file_manager() -> PacBioRunFileManager:
    return PacBioRunFileManager()


@pytest.fixture
def pacbio_run_names_service(pac_bio_runs_dir: Path) -> PacbioRunNamesService:
    return PacbioRunNamesService(run_directory=pac_bio_runs_dir.as_posix())


@pytest.fixture
def pac_bio_metrics_parser(pac_bio_run_file_manager: PacBioRunFileManager) -> PacBioMetricsParser:
    return PacBioMetricsParser(file_manager=pac_bio_run_file_manager)


@pytest.fixture
def pac_bio_data_transfer_service(
    pac_bio_metrics_parser: PacBioMetricsParser,
    pac_bio_run_file_manager: PacBioRunFileManager,
) -> PacBioDataTransferService:
    return PacBioDataTransferService(metrics_service=pac_bio_metrics_parser)


@pytest.fixture
def pac_bio_store_service(
    store: Store, pac_bio_data_transfer_service: PacBioDataTransferService
) -> PacBioStoreService:
    return PacBioStoreService(store=store, data_transfer_service=pac_bio_data_transfer_service)


@pytest.fixture
def pac_bio_post_processing_service(
    pac_bio_run_data_generator: PacBioRunDataGenerator,
    pac_bio_housekeeper_service: PacBioHousekeeperService,
    pac_bio_store_service: PacBioStoreService,
    pac_bio_runs_dir: Path,
) -> PacBioPostProcessingService:
    return PacBioPostProcessingService(
        run_validator=Mock(),
        run_data_generator=pac_bio_run_data_generator,
        hk_service=pac_bio_housekeeper_service,
        store_service=pac_bio_store_service,
        sequencing_dir=pac_bio_runs_dir.as_posix(),
    )


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
