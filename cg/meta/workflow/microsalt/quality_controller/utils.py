from cg.constants.constants import MicrosaltAppTags, MicrosaltQC
from cg.meta.workflow.microsalt.metrics_parser.models import SampleMetrics
from cg.meta.workflow.microsalt.quality_controller.models import QualityResult
from cg.models.orders.sample_base import ControlEnum
from cg.store.models import Sample


def is_valid_total_reads(reads: int, target_reads: int) -> bool:
    return reads > target_reads * MicrosaltQC.TARGET_READS_FAIL_THRESHOLD


def is_valid_total_reads_for_control(reads: int, target_reads: int) -> bool:
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


def get_negative_control_result(results: list[QualityResult]) -> QualityResult:
    for result in results:
        if result.is_control:
            return result
    raise ValueError("No negative control found")


def negative_control_pass_qc(results: list[QualityResult]) -> bool:
    negative_control_result: QualityResult = get_negative_control_result(results)
    return negative_control_result.passes_qc


def get_results_passing_qc(results: list[QualityResult]) -> list[QualityResult]:
    return [result for result in results if result.passes_qc]


def get_non_urgent_results(results: list[QualityResult]) -> list[QualityResult]:
    return [result for result in results if result.application_tag != MicrosaltAppTags.MWRNXTR003]


def get_urgent_results(results: list[QualityResult]) -> list[QualityResult]:
    return [result for result in results if result.application_tag == MicrosaltAppTags.MWRNXTR003]


def urgent_samples_pass_qc(results: list[QualityResult]) -> bool:
    urgent_results: list[QualityResult] = get_urgent_results(results)
    return all(result.passes_qc for result in urgent_results)


def non_urgent_samples_pass_qc(results: list[QualityResult]) -> bool:
    non_urgent_samples: list[QualityResult] = get_non_urgent_results(results)
    passing_qc: list[QualityResult] = get_results_passing_qc(non_urgent_samples)

    if not non_urgent_samples:
        return True

    fraction_passing_qc: float = len(passing_qc) / len(non_urgent_samples)
    return fraction_passing_qc >= MicrosaltQC.QC_PERCENT_THRESHOLD_MWX


def is_sample_negative_control(sample: Sample) -> bool:
    return sample.control == ControlEnum.negative


def get_application_tag(sample: Sample) -> str:
    return sample.application_version.application.tag
