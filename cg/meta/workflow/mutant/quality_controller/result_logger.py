import logging
from pathlib import Path
from cg.meta.workflow.mutant.quality_controller.models import (
    CaseQualityResult,
    SampleQualityResults,
    SamplesQualityResults,
)

LOG = logging.getLogger(__name__)


class ResultLogger:
    @staticmethod
    def log_results(
        case_quality_result: CaseQualityResult,
        samples_quality_results: SamplesQualityResults,
        report: Path,
    ) -> None:
        if case_quality_result.passes_qc:
            case_message = f"QC passed, see {report} for details."
        else:
            case_message = get_case_fail_message(case_quality_result)
        LOG.warning(case_message)

        samples_message = samples_results_message(samples_quality_results)
        LOG.info(samples_message)

    @staticmethod
    def log_sample_result(result: SampleQualityResults) -> None:
        control_message = ""
        if result.is_external_negative_control:
            control_message = "External negative control sample "
        if result.is_internal_negative_control:
            control_message = "Internal negative control sample "
        if result.passes_qc:
            message = f"{control_message}{result.sample_id} passed QC."
            LOG.info(message)
        else:
            message = f"{control_message}{result.sample_id} failed QC."
            LOG.warning(message)

    @staticmethod
    def log_case_result(result: CaseQualityResult) -> None:
        if not result.passes_qc:
            LOG.warning("Case failed QC.")
        else:
            LOG.warning("Case passed QC.")


def get_case_fail_message(case_quality_result: CaseQualityResult) -> str:
    fail_reasons = []
    if not case_quality_result.internal_negative_control_passes_qc:
        fail_reasons.append("The internal negative control sample failed QC.\n")
    if not case_quality_result.external_negative_control_passes_qc:
        fail_reasons.append("The external negative control sample failed QC.\n")

    fail_message = "QC failed."

    return fail_message + "\n".join(fail_reasons)


def samples_results_message(samples_quality_results: SamplesQualityResults) -> str:
    internal_negative_control_message: str = (
        "Internal negative control sample " + "passed QC. "
        if samples_quality_results.internal_negative_control.passes_qc
        else "failed QC. "
    )
    external_negative_control_message: str = (
        "External negative control sample " + "passed QC. "
        if samples_quality_results.external_negative_control.passes_qc
        else "failed QC. "
    )

    samples_message: str = f"Sample results: {samples_quality_results.total_samples_count} total, {samples_quality_results.failed_samples_count} failed, {samples_quality_results.passed_samples_count} passed."

    return "\n".join(
        [internal_negative_control_message, external_negative_control_message, samples_message]
    )
