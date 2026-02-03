import pytest

from cg.constants.devices import DeviceType
from cg.services.run_devices.pacbio.data_transfer_service.dto import (
    PacBioDTOs,
    PacBioSampleSequencingMetricsDTO,
    PacBioSequencingRunDTO,
    PacBioSMRTCellDTO,
    PacBioSMRTCellMetricsDTO,
)


@pytest.fixture
def pac_bio_smrt_cell_dto(barcoded_smrt_cell_internal_id: str) -> PacBioSMRTCellDTO:
    return PacBioSMRTCellDTO(type=DeviceType.PACBIO, internal_id=barcoded_smrt_cell_internal_id)


@pytest.fixture
def pacbio_sequencing_run_dto(pacbio_barcoded_run_id: str) -> PacBioSequencingRunDTO:
    return PacBioSequencingRunDTO(
        instrument_name="Wilma",  # type: ignore
        run_id=pacbio_barcoded_run_id,
        run_name="run-name",
        unique_id="unique-id",
    )


@pytest.fixture
def pacbio_smrt_cell_metrics_dto(
    pacbio_barcoded_run_id: str,
    pacbio_barcoded_1_c01_movie_name: str,
) -> PacBioSMRTCellMetricsDTO:
    sample_data = {
        "type": DeviceType.PACBIO,
        "well": "C01",
        "plate": 1,
        "run_id": pacbio_barcoded_run_id,
        "started_at": "2024-09-13T16:21:15",
        "completed_at": "2024-09-15T14:11:32.418Z",
        "movie_time_hours": 10,
        "hifi_reads": 7815301,
        "hifi_yield": 115338856495,
        "hifi_mean_read_length": 14758,
        "hifi_median_read_length": 14679,
        "hifi_mean_length_n50": 14679,
        "hifi_median_read_quality": "Q35",
        "percent_reads_passing_q30": 93.10000000000001,
        "productive_zmws": 25165824,
        "p0_percent": round((6257733 / 25165824) * 100, 0),
        "p1_percent": round((18766925 / 25165824) * 100, 0),
        "p2_percent": round((141166 / 25165824) * 100, 0),
        "polymerase_mean_read_length": 85641,
        "polymerase_read_length_n50": 168750,
        "polymerase_mean_longest_subread": 18042,
        "polymerase_longest_subread_n50": 21750,
        "control_reads": 2368,
        "control_mean_read_length": 69936,
        "control_mean_read_concordance": 90.038,
        "control_mode_read_concordance": 91.0,
        "failed_reads": 469053,
        "failed_yield": 7404831038,
        "failed_mean_read_length": 15786,
        "barcoded_hifi_reads": 7785983,
        "barcoded_hifi_reads_percentage": 99.62486409672513,
        "barcoded_hifi_yield": 114676808325,
        "barcoded_hifi_yield_percentage": 99.63122400514475,
        "barcoded_hifi_mean_read_length": 14728,
        "unbarcoded_hifi_reads": 29318,
        "unbarcoded_hifi_yield": 424465869,
        "unbarcoded_hifi_mean_read_length": 14477,
        "movie_name": pacbio_barcoded_1_c01_movie_name,
    }
    return PacBioSMRTCellMetricsDTO(**sample_data)


@pytest.fixture
def pac_bio_sample_sequencing_metrics_dto(
    pacbio_barcoded_sample_internal_id: str,
) -> list[PacBioSampleSequencingMetricsDTO]:
    sample_metrics_data = {
        "sample_internal_id": pacbio_barcoded_sample_internal_id,
        "hifi_reads": 7785983,
        "hifi_yield": 114676808325,
        "hifi_mean_read_length": 14728,
        "hifi_median_read_quality": "Q35",
        "polymerase_mean_read_length": 163451,
    }
    return [PacBioSampleSequencingMetricsDTO(**sample_metrics_data)]


@pytest.fixture
def pac_bio_dtos(
    pacbio_sequencing_run_dto: PacBioSequencingRunDTO,
    pac_bio_smrt_cell_dto: PacBioSMRTCellDTO,
    pacbio_smrt_cell_metrics_dto: PacBioSMRTCellMetricsDTO,
    pac_bio_sample_sequencing_metrics_dto: list[PacBioSampleSequencingMetricsDTO],
) -> PacBioDTOs:
    return PacBioDTOs(
        sequencing_run=pacbio_sequencing_run_dto,
        run_device=pac_bio_smrt_cell_dto,
        smrt_cell_metrics=pacbio_smrt_cell_metrics_dto,
        sample_sequencing_metrics=pac_bio_sample_sequencing_metrics_dto,
    )
