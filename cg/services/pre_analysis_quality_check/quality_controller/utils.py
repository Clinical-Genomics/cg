from typing import Callable

from cg.services.pre_analysis_quality_check.quality_controller.quality_controller import (
    QualityController,
)
from cg.services.pre_analysis_quality_check.quality_check_mapper.quality_check_mapper import WorkflowQualityCheckMapper
from cg.store.models import Case, Sample




def run_pre_analysis_quality_check(
    obj: Case | Sample,
    quality_checks: list[Callable],
) -> bool:
    return QualityController.run_qc(obj, quality_checks)


def run_case_pre_analysis_quality_check(
    case: Case,
) -> bool:
    quality_checks: list[Callable] = WorkflowQualityCheckMapper.get_quality_checks_for_workflow(
        workflow=case.data_analysis
    )
    return QualityController.run_qc(obj=case, quality_checks=quality_checks)


def run_sample_sequencing_quality_check(sample: Sample) -> bool:
    quality_checks: list[Callable] = WorkflowQualityCheckMapper.get_sample_quality_checks()
    return run_pre_analysis_quality_check(obj=sample, quality_checks=quality_checks)
