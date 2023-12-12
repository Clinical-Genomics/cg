from pathlib import Path

from cg.constants.constants import MicrosaltAppTags, MicrosaltQC
from cg.io.json import read_json
from cg.meta.workflow.microsalt.models import QualityMetrics, QualityResult
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


def parse_quality_metrics(file_path: Path) -> QualityMetrics:
    data = read_json(file_path)
    return QualityMetrics.model_validate_json(data)


def is_sample_negative_control(sample: Sample) -> bool:
    return sample.control == ControlEnum.negative


def get_application_tag(sample: Sample) -> str:
    return sample.application_version.application.tag


def get_urgent_results(results: list[QualityResult]) -> list[QualityResult]:
    return [result for result in results if result.application_tag == MicrosaltAppTags.MWRNXTR003]


def get_non_urgent_results(results: list[QualityResult]) -> list[QualityResult]:
    return [result for result in results if result.application_tag != MicrosaltAppTags.MWRNXTR003]


def get_results_passing_qc(results: list[QualityResult]) -> list[QualityResult]:
    return [result for result in results if result.passes_qc]


def get_negative_control_result(results: list[QualityResult]) -> QualityResult:
    for result in results:
        if result.is_negative_control:
            return result
