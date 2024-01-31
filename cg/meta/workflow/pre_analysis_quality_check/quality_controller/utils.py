from typing import Callable

from cg.meta.workflow.pre_analysis_quality_check.quality_controller.quality_controller import (
    QualityController,
)
from cg.meta.workflow.pre_analysis_quality_check.sequencing_quality_metrics.constants import (
    SEQUENCING_QUALITY_CHECKS,
)
from cg.store.models import Case


def run_pre_analysis_quality_check(
    case: Case,
) -> bool:
    sequencing_quality_checks: list[Callable] = SEQUENCING_QUALITY_CHECKS.get(
        type(case.data_analysis)
    )
    if not sequencing_quality_checks:
        raise NotImplementedError(
            f"No sequencing quality check have implemented for workflow {case.data_analysis}."
        )

    return QualityController.run_qc(case, sequencing_quality_checks)
