from datetime import datetime
from unittest.mock import Mock

import pytest

from cg.constants.devices import DeviceType
from cg.services.run_devices.pacbio.data_storage_service.pacbio_store_service import (
    PacBioStoreService,
)
from cg.services.run_devices.pacbio.data_transfer_service.data_transfer_service import (
    PacBioDataTransferService,
)
from cg.services.run_devices.pacbio.data_transfer_service.dto import (
    PacBioDTOs,
    PacBioSampleSequencingMetricsDTO,
    PacBioSequencingRunDTO,
    PacBioSMRTCellDTO,
)
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


@pytest.fixture
def pac_bio_smrt_cell_dto() -> PacBioSMRTCellDTO:
    return PacBioSMRTCellDTO(type=DeviceType.PACBIO, internal_id="internal_id")


@pytest.fixture
def pac_bio_sequencing_run_dto() -> PacBioSequencingRunDTO:
    sample_data = {
        "type": DeviceType.PACBIO,
        "well": "A1",
        "plate": 1,
        "started_at": datetime.now(),
        "completed_at": datetime.now(),
        "movie_time_hours": 10,
        "hifi_reads": 500000,
        "hifi_yield": 3000000000,
        "hifi_mean_read_length": 6000,
        "hifi_median_read_length": 6000,
        "hifi_mean_length_n50": 5000,
        "hifi_median_read_quality": "Q20",
        "percent_reads_passing_q30": 99.5,
        "productive_zmws": 150000,
        "p0_percent": 0.5,
        "p1_percent": 1.5,
        "p2_percent": 98.0,
        "polymerase_mean_read_length": 7000,
        "polymerase_read_length_n50": 6500,
        "polymerase_mean_longest_subread": 12000,
        "polymerase_longest_subread_n50": 11000,
        "control_reads": 10000,
        "control_mean_read_length": 5000,
        "control_mean_read_concordance": 99.0,
        "control_mode_read_concordance": 99.5,
        "failed_reads": 1000,
        "failed_yield": 500000000,
        "failed_mean_read_length": 3000,
        "movie_name": "movie123",
    }
    return PacBioSequencingRunDTO(**sample_data)


@pytest.fixture
def pac_bio_sample_sequencing_metrics_dto() -> list[PacBioSampleSequencingMetricsDTO]:
    sample_metrics_data = {
        "sample_internal_id": "sample_123",
        "hifi_reads": 450000,
        "hifi_yield": 2750000000,
        "hifi_mean_read_length": 6100,
        "hifi_median_read_length": 6000,
        "hifi_median_read_quality": "Q30",
        "percent_reads_passing_q30": 98.6,
        "failed_reads": 1500,
        "failed_yield": 500000000,
        "failed_mean_read_length": 3200,
    }
    return [PacBioSampleSequencingMetricsDTO(**sample_metrics_data)]


@pytest.fixture
def pac_bio_dtos(
    pac_bio_smrt_cell_dto: PacBioSMRTCellDTO,
    pac_bio_sequencing_run_dto: PacBioSequencingRunDTO,
    pac_bio_sample_sequencing_metrics_dto: list[PacBioSampleSequencingMetricsDTO],
) -> PacBioDTOs:
    return PacBioDTOs(
        run_device=pac_bio_smrt_cell_dto,
        sequencing_run=pac_bio_sequencing_run_dto,
        sample_sequencing_metrics=pac_bio_sample_sequencing_metrics_dto,
    )


@pytest.fixture
def pac_bio_store_service(store: Store, helpers: StoreHelpers, pac_bio_dtos: PacBioDTOs):
    helpers.add_sample(
        store=store, internal_id=pac_bio_dtos.sample_sequencing_metrics[0].sample_internal_id
    )
    return PacBioStoreService(
        store=store, data_transfer_service=PacBioDataTransferService(metrics_service=Mock())
    )
