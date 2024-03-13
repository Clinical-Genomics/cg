from cg.constants.constants import MutantQC
from cg.meta.workflow.mutant.quality_controller.models import CaseQualityResult, SampleQualityResult
from cg.models.orders.sample_base import ControlEnum
from cg.store.models import Sample


def is_valid_total_reads(reads: int, target_reads: int, threshold_percentage: int) -> bool:
    return reads > target_reads * threshold_percentage / 100


def is_sample_external_negative_control(sample: Sample) -> bool:
    return sample.control == ControlEnum.negative


def is_valid_total_reads_for_external_negative_control(reads: int, target_reads: int) -> bool:
    return reads < target_reads * MutantQC.EXTERNAL_NEGATIVE_CONTROL_READS_THRESHOLD


def get_external_negative_control_result(
    results: list[SampleQualityResult]
) -> SampleQualityResult | None:
    for result in results:
        if result.is_control:
            return result


def external_negative_control_pass_qc(results: list[SampleQualityResult]) -> bool:
    if negative_control_result := get_external_negative_control_result(results):
        return negative_control_result.passes_qc
    return True


def get_sample_target_reads(sample: Sample) -> int:
    return sample.application_version.application.target_reads


def get_percent_reads_guaranteed(sample: Sample) -> int:
    return sample.application_version.application.percent_reads_guaranteed
