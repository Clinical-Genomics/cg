import logging
from cg.meta.workflow.microsalt.quality_controller.models import CaseQualityResult, QualityResult

LOG = logging.getLogger(__name__)


class ResultLogger:
    @staticmethod
    def log_results(sample_results: list[QualityResult], case_result: CaseQualityResult):
        if case_result.passes_qc:
            LOG.info("Quality control passed.\n")
        else:
            message = get_case_fail_message(case_result)
            LOG.warning(message)

        message = sample_result_message(sample_results)
        LOG.info(message)


def get_case_fail_message(case_result: CaseQualityResult) -> str:
    fail_reasons = []

    if not case_result.control_passes_qc:
        fail_reasons.append("The negative control sample failed quality control.\n")
    if not case_result.urgent_passes_qc:
        fail_reasons.append("The urgent samples failed quality control.\n")
    if not case_result.non_urgent_passes_qc:
        fail_reasons.append("The non-urgent samples failed quality control.\n")

    fail_message = "Quality control failed.\n"

    return fail_message + " ".join(fail_reasons)


def sample_result_message(sample_results: list[QualityResult]) -> str:
    failed_samples: list[QualityResult] = get_failed_results(sample_results)
    passed_samples: list[QualityResult] = get_passed_results(sample_results)

    failed_count: int = len(failed_samples)
    passed_count: int = len(passed_samples)
    total_count = len(sample_results)

    return f"Sample results: {failed_count} failed, {passed_count} passed, {total_count} total.\n"


def get_failed_results(results: list[QualityResult]) -> list[str]:
    return [result for result in results if not result.passes_qc]


def get_passed_results(results: list[QualityResult]) -> list[str]:
    return [result for result in results if result.passes_qc]
