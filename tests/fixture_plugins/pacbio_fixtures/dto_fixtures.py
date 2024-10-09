from datetime import datetime

import pytest

from cg.constants.devices import DeviceType
from cg.services.run_devices.pacbio.data_transfer_service.dto import (
    PacBioDTOs,
    PacBioSampleSequencingMetricsDTO,
    PacBioSequencingRunDTO,
    PacBioSMRTCellDTO,
)


@pytest.fixture
def pac_bio_smrt_cell_dto() -> PacBioSMRTCellDTO:
    return PacBioSMRTCellDTO(type=DeviceType.PACBIO, internal_id="internal_id")


@pytest.fixture
def pac_bio_sequencing_run_dto(pac_bio_test_run_name: str) -> PacBioSequencingRunDTO:
    sample_data = {
        "type": DeviceType.PACBIO,
        "well": "A1",
        "plate": 1,
        "run_name": pac_bio_test_run_name,
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
        "barcoded_hifi_reads": 450000,
        "barcoded_hifi_reads_percentage": 95.6,
        "barcoded_hifi_yield": 1025000000,
        "barcoded_hifi_yield_percentage": 96.7,
        "barcoded_hifi_mean_read_length": 6100,
        "unbarcoded_hifi_reads": 50000,
        "unbarcoded_hifi_yield": 1975000000,
        "unbarcoded_hifi_mean_read_length": 6200,
        "movie_name": "movie123",
    }
    return PacBioSequencingRunDTO(**sample_data)


@pytest.fixture
def pac_bio_sample_sequencing_metrics_dto(
    pacbio_barcoded_sample_internal_id: str,
) -> list[PacBioSampleSequencingMetricsDTO]:
    sample_metrics_data = {
        "sample_internal_id": pacbio_barcoded_sample_internal_id,
        "hifi_reads": 450000,
        "hifi_yield": 2750000000,
        "hifi_mean_read_length": 6100,
        "hifi_median_read_quality": "Q30",
        "polymerase_mean_read_length": 70000,
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
