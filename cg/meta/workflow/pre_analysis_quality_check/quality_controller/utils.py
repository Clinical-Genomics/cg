from typing import Callable

from cg.meta.workflow.pre_analysis_quality_check.quality_controller.quality_controller import (
    CaseQualityController,
    SampleQualityController
)
from cg.meta.workflow.pre_analysis_quality_check.sequencing_quality_metrics.constants import (
    CASE_SEQUENCING_QUALITY_CHECKS,
    SAMPLE_SEQUENCING_QUALITY_CHECKS
)
from cg.store.models import Case, Sample

def run_pre_analysis_quality_check(
    obj, quality_checks_dict, quality_controller
) -> bool:
    sequencing_quality_checks = quality_checks_dict.get(type(obj.data_analysis))
    if not sequencing_quality_checks:
        raise NotImplementedError(
            f"No sequencing quality check have implemented for workflow {obj.data_analysis}."
        )

    return quality_controller.run_qc(obj, sequencing_quality_checks)

def run_case_pre_analysis_quality_check(
    case: Case,
) -> bool:
    return run_pre_analysis_quality_check(
        case, CASE_SEQUENCING_QUALITY_CHECKS, CaseQualityController
    )

def run_sample_sequencing_quality_check(
    sample: Sample
) -> bool:
    return run_pre_analysis_quality_check(
        sample, SAMPLE_SEQUENCING_QUALITY_CHECKS, SampleQualityController
    )