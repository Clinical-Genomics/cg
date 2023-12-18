import logging
from cg.meta.workflow.microsalt.quality_controller.models import (
    CaseQualityResult,
    SampleQualityResult,
)

LOG = logging.getLogger(__name__)


class ResultLogger:
    @staticmethod
    def log_results(samples: list[SampleQualityResult], case: CaseQualityResult) -> None:
        if case.passes_qc:
            LOG.info("Quality control passed.")
        else:
            message = get_case_fail_message(case)
            LOG.warning(message)

        message = sample_result_message(samples)
        LOG.info(message)


def get_case_fail_message(case: CaseQualityResult) -> str:
    fail_reasons = []

    if not case.control_passes_qc:
        fail_reasons.append("The negative control sample failed quality control.\n")
    if not case.urgent_passes_qc:
        fail_reasons.append("The urgent samples failed quality control.\n")
    if not case.non_urgent_passes_qc:
        fail_reasons.append("The non-urgent samples failed quality control.\n")

    fail_message = "Quality control failed.\n"

    return fail_message + " ".join(fail_reasons)


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
