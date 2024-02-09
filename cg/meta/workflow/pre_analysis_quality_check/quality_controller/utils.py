from typing import Callable

from cg.meta.workflow.pre_analysis_quality_check.quality_controller.quality_controller import (
    QualityController,
)
from cg.meta.workflow.pre_analysis_quality_check.sequencing_quality_metrics.constants import (
    CASE_SEQUENCING_QUALITY_CHECKS,
    SAMPLE_SEQUENCING_QUALITY_CHECKS,
)
from cg.store.models import Case, Sample


def _get_sequencing_quality_checks_for_case(
    data_analysis: str,
) -> list[Callable] | None:
    sequencing_quality_checks: list[Callable] | None = CASE_SEQUENCING_QUALITY_CHECKS.get(
        data_analysis, None
    )
    if not sequencing_quality_checks:
        raise NotImplementedError(
            f"No sequencing quality check have implemented for workflow {data_analysis}."
        )
    return sequencing_quality_checks


def run_pre_analysis_quality_check(
    obj: Case | Sample,
    quality_checks: list[Callable],
) -> bool:
    return QualityController.run_qc(obj, quality_checks)


def run_case_pre_analysis_quality_check(
    case: Case,
) -> bool:
    sequencing_quality_checks: list[Callable] | None = _get_sequencing_quality_checks_for_case(
        case.data_analysis
    )

    quality_checks: list[Callable] = sequencing_quality_checks
    return run_pre_analysis_quality_check(obj=case, quality_checks=quality_checks)


def run_sample_sequencing_quality_check(sample: Sample) -> bool:
    quality_checks: list[Callable] = SAMPLE_SEQUENCING_QUALITY_CHECKS
    return run_pre_analysis_quality_check(obj=sample, quality_checks=quality_checks)
