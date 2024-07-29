"""Data transfer objects for the PacbioDataTransferService."""

from pydantic import BaseModel

from cg.constants.devices import DeviceType
from cg.services.post_processing.abstract_models import PostProcessingDTOs


class PacBioSequencingRunDTO(BaseModel):
    type: DeviceType
    well: str
    plate: int
    movie_time_hours: int
    hifi_reads: int
    hifi_yield: int
    hifi_mean_read_length: int
    hifi_median_read_quality: str
    percent_reads_passing_q30: float
    productive_zmws: int
    p0_percent: float
    p1_percent: float
    p2_percent: float
    polymerase_mean_read_length: int
    polymerase_read_length_n50: int
    polymerase_mean_longest_subread: int
    polymerase_longest_subread_n50: int
    control_reads: int
    control_mean_read_length: int
    control_mean_read_concordance: float
    control_mode_read_concordance: float
    failed_reads: int
    failed_yield: int
    failed_mean_read_length: int
    movie_name: str


class PacBioSMRTCellDTO(BaseModel):
    type: DeviceType
    internal_id: str


class PacBioSampleSequencingMetricsDTO(BaseModel):
    hifi_reads: int
    hifi_yield: int
    hifi_mean_read_length: int
    hifi_median_read_quality: str
    percent_reads_passing_q30: float
    failed_reads: int
    failed_yield: int
    failed_mean_read_length: int


class PacBioDTOs(PostProcessingDTOs):
    run_device: PacBioSMRTCellDTO
    sequencing_run: PacBioSequencingRunDTO
    sample_sequencing_metrics: list[PacBioSampleSequencingMetricsDTO]