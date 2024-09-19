from cg.constants.devices import DeviceType
from cg.services.run_devices.pacbio.data_transfer_service.dto import (
    PacBioSampleSequencingMetricsDTO,
    PacBioSequencingRunDTO,
    PacBioSMRTCellDTO,
)
from cg.services.run_devices.pacbio.metrics_parser.models import PacBioMetrics


def get_smrt_cell_dto(metrics: PacBioMetrics) -> PacBioSMRTCellDTO:
    internal_id: str = metrics.dataset_metrics.cell_id
    return PacBioSMRTCellDTO(type=DeviceType.PACBIO, internal_id=internal_id)


def get_sequencing_run_dto(metrics: PacBioMetrics) -> PacBioSequencingRunDTO:
    hifi_mean_read_quality: str = f"Q{metrics.read.hifi_median_read_quality}"
    return PacBioSequencingRunDTO(
        type=DeviceType.PACBIO,
        well=metrics.dataset_metrics.well,
        plate=metrics.dataset_metrics.plate,
        started_at=metrics.dataset_metrics.run_started_at,
        completed_at=metrics.dataset_metrics.run_completed_at,
        hifi_reads=metrics.read.hifi_reads,
        hifi_yield=metrics.read.hifi_yield,
        hifi_mean_read_length=metrics.read.hifi_mean_read_length,
        hifi_median_read_length=metrics.read.hifi_median_read_length,
        hifi_median_read_quality=hifi_mean_read_quality,
        hifi_mean_length_n50=metrics.read.hifi_mean_length_n50,
        percent_reads_passing_q30=metrics.read.percent_q30,
        productive_zmws=metrics.productivity.productive_zmws,
        p0_percent=metrics.productivity.percent_p_0,
        p1_percent=metrics.productivity.percent_p_1,
        p2_percent=metrics.productivity.percent_p_2,
        polymerase_mean_read_length=metrics.polymerase.mean_read_length,
        polymerase_read_length_n50=metrics.polymerase.read_length_n50,
        polymerase_mean_longest_subread=metrics.polymerase.mean_longest_subread_length,
        polymerase_longest_subread_n50=metrics.polymerase.longest_subread_length_n50,
        control_reads=metrics.control.reads,
        control_mean_read_length=metrics.control.mean_read_length,
        control_mean_read_concordance=metrics.control.percent_mean_concordance_reads,
        control_mode_read_concordance=metrics.control.percent_mode_concordance_reads,
        failed_reads=metrics.read.failed_reads,
        failed_yield=metrics.read.failed_yield,
        failed_mean_read_length=metrics.read.failed_mean_read_length,
        movie_name=metrics.dataset_metrics.movie_name,
    )


def get_sample_sequencing_metrics_dtos(
    metrics: PacBioMetrics,
) -> list[PacBioSampleSequencingMetricsDTO]:
    hifi_mean_read_quality: str = f"Q{metrics.read.hifi_median_read_quality}"
    sample_sequencing_metrics_dto = PacBioSampleSequencingMetricsDTO(
        sample_internal_id=metrics.dataset_metrics.sample_internal_id,
        hifi_reads=metrics.read.hifi_reads,
        hifi_yield=metrics.read.hifi_yield,
        hifi_mean_read_length=metrics.read.hifi_mean_read_length,
        hifi_median_read_length=metrics.read.hifi_median_read_length,
        hifi_median_read_quality=hifi_mean_read_quality,
        percent_reads_passing_q30=metrics.read.percent_q30,
        failed_reads=metrics.read.failed_reads,
        failed_yield=metrics.read.failed_yield,
        failed_mean_read_length=metrics.read.failed_mean_read_length,
    )
    return [sample_sequencing_metrics_dto]
