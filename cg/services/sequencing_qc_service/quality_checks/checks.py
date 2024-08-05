from typing import Callable
from enum import Enum

from cg.constants import Workflow
from cg.store.models import Case
from cg.services.sequencing_qc_service.quality_checks.utils import (
    case_pass_sequencing_qc,
    sample_pass_sequencing_qc,
    any_sample_in_case_has_reads,
)


class QualityCheck(Enum):
    """
    Parent class for the quality checks.
    """


class SequencingQCCheck(QualityCheck):
    CASE_PASSES: Callable = case_pass_sequencing_qc
    SAMPLE_PASSES: Callable = sample_pass_sequencing_qc
    ANY_SAMPLE_IN_CASE_HAS_READS: Callable = any_sample_in_case_has_reads


def get_sequencing_quality_check_for_case(case: Case) -> Callable:
    """Return the appropriate sequencing quality checks for the workflow for a case."""
    workflow: Workflow = case.data_analysis

    case_passes_workflows = [
        Workflow.BALSAMIC,
        Workflow.BALSAMIC_PON,
        Workflow.BALSAMIC_QC,
        Workflow.BALSAMIC_UMI,
        Workflow.MIP_DNA,
        Workflow.MIP_RNA,
        Workflow.RAREDISEASE,
        Workflow.RNAFUSION,
        Workflow.TOMTE,
    ]

    any_sample_in_case_has_reads_workflows = [
        Workflow.FLUFFY,
        Workflow.FASTQ,
        Workflow.MICROSALT,
        Workflow.MUTANT,
        Workflow.TAXPROFILER,
    ]

    if workflow in case_passes_workflows:
        return SequencingQCCheck.CASE_PASSES
    elif workflow in any_sample_in_case_has_reads_workflows:
        return SequencingQCCheck.ANY_SAMPLE_IN_CASE_HAS_READS
    raise ValueError(f"Workflow {workflow} does not have a sequencing quality check.")


def get_sample_sequencing_quality_check() -> Callable:
    return SequencingQCCheck.SAMPLE_PASSES


def run_quality_checks(quality_checks: list[QualityCheck], **kwargs) -> bool:
    return all(quality_check(**kwargs) for quality_check in quality_checks)
