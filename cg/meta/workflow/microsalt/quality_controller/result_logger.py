import logging
from pathlib import Path
from cg.meta.workflow.microsalt.quality_controller.models import (
    CaseQualityResult,
    SampleQualityResult,
)

LOG = logging.getLogger(__name__)


class ResultLogger:
    @staticmethod
    def log_results(
        samples: list[SampleQualityResult], case: CaseQualityResult, report: Path
    ) -> None:
        if case.passes_qc:
            LOG.info(f"QC passed, see {report} for details.")
        else:
            message = get_case_fail_message(case)
            LOG.warning(message)

        message = sample_result_message(samples)
        LOG.info(message)

    @staticmethod
    def log_sample_result(result: SampleQualityResult) -> None:
        control_message = "Control sample " if result.is_control else ""
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


def get_case_fail_message(case: CaseQualityResult) -> str:
    fail_reasons = []

    if not case.control_passes_qc:
        fail_reasons.append("The negative control sample failed QC.\n")
    if not case.urgent_passes_qc:
        fail_reasons.append("The urgent samples failed QC.\n")
    if not case.non_urgent_passes_qc:
        fail_reasons.append("The non-urgent samples failed QC.\n")
    fail_message = "QC failed.\n"
    return fail_message + "".join(fail_reasons)


def sample_result_message(samples: list[SampleQualityResult]) -> str:
    failed_samples: list[SampleQualityResult] = get_failed_results(samples)
    passed_samples: list[SampleQualityResult] = get_passed_results(samples)

    failed_count: int = len(failed_samples)
    passed_count: int = len(passed_samples)
    total_count: int = len(samples)

    return f"Sample results: {failed_count} failed, {passed_count} passed, {total_count} total."


def get_failed_results(samples: list[SampleQualityResult]) -> list[str]:
    return [result for result in samples if not result.passes_qc]


def get_passed_results(samples: list[SampleQualityResult]) -> list[str]:
    return [result for result in samples if result.passes_qc]
