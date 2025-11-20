from pathlib import Path

from cg.constants.constants import MicrosaltQC
from cg.meta.workflow.microsalt.constants import QUALITY_REPORT_FILE_NAME
from cg.meta.workflow.microsalt.metrics_parser.models import SampleMetrics
from cg.meta.workflow.microsalt.quality_controller.models import (
    CaseQualityResult,
    SampleQualityResult,
)
from cg.meta.workflow.microsalt.quality_controller.result_logger import ResultLogger
from cg.models.orders.sample_base import ControlEnum
from cg.store.models import Sample


def is_valid_total_reads(reads: int, target_reads: int, threshold_percentage: int) -> bool:
    return reads > target_reads * threshold_percentage / 100


def is_valid_total_reads_for_negative_control(reads: int, target_reads: int) -> bool:
    return reads < target_reads * MicrosaltQC.NEGATIVE_CONTROL_READS_THRESHOLD


def is_valid_mapping_rate(mapping_rate: float) -> bool:
    return mapping_rate > MicrosaltQC.MAPPED_RATE_THRESHOLD


def is_valid_duplication_rate(duplication_rate: float) -> bool:
    return duplication_rate < MicrosaltQC.DUPLICATION_RATE_THRESHOLD


def is_valid_median_insert_size(insert_size: int) -> bool:
    return insert_size > MicrosaltQC.INSERT_SIZE_THRESHOLD


def is_valid_average_coverage(average_coverage: float) -> bool:
    return average_coverage > MicrosaltQC.AVERAGE_COVERAGE_THRESHOLD


def is_valid_10x_coverage(coverage_10x: float) -> bool:
    return coverage_10x > MicrosaltQC.COVERAGE_10X_THRESHOLD


def has_valid_mapping_rate(metrics: SampleMetrics) -> bool:
    mapped_rate: float | None = metrics.microsalt_samtools_stats.mapped_rate
    return is_valid_mapping_rate(mapped_rate) if mapped_rate else False


def has_valid_duplication_rate(metrics: SampleMetrics) -> bool:
    duplication_rate: float | None = metrics.picard_markduplicate.duplication_rate
    return is_valid_duplication_rate(duplication_rate) if duplication_rate else False


def has_valid_median_insert_size(metrics: SampleMetrics) -> bool:
    insert_size: int | None = metrics.picard_markduplicate.insert_size
    return is_valid_median_insert_size(insert_size) if insert_size else False


def has_valid_average_coverage(metrics: SampleMetrics) -> bool:
    coverage: float | None = metrics.microsalt_samtools_stats.average_coverage
    return is_valid_average_coverage(coverage) if coverage else False


def has_valid_10x_coverage(metrics: SampleMetrics) -> bool:
    coverage_10x: float | None = metrics.microsalt_samtools_stats.coverage_10x
    return is_valid_10x_coverage(coverage_10x) if coverage_10x else False


def get_negative_control_result(results: list[SampleQualityResult]) -> SampleQualityResult | None:
    for result in results:
        if result.is_control:
            return result


def negative_control_pass_qc(results: list[SampleQualityResult]) -> bool:
    if negative_control_result := get_negative_control_result(results):
        return negative_control_result.passes_qc
    return True


def is_sample_negative_control(sample: Sample) -> bool:
    return sample.control == ControlEnum.negative


def get_application_tag(sample: Sample) -> str:
    return sample.application_version.application.tag


def get_sample_target_reads(sample: Sample) -> int:
    return sample.application_version.application.target_reads


def get_percent_reads_guaranteed(sample: Sample) -> int:
    return sample.application_version.application.percent_reads_guaranteed


def get_report_path(metrics_file_path: Path) -> Path:
    return metrics_file_path.parent.joinpath(QUALITY_REPORT_FILE_NAME)


def quality_control_case(sample_results: list[SampleQualityResult]) -> CaseQualityResult:
    control_pass_qc: bool = negative_control_pass_qc(sample_results)
    case_passes_qc: bool = all(sample.passes_qc for sample in sample_results)
    result = CaseQualityResult(
        passes_qc=case_passes_qc,
        control_passes_qc=control_pass_qc,
    )
    ResultLogger.log_case_result(result)
    return result
