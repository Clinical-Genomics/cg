from enum import Enum
from typing import Callable

from cg.constants import Workflow
from cg.services.sequencing_qc_service.quality_checks.utils import (
    all_samples_in_case_have_reads,
    any_sample_in_case_has_reads,
    case_pass_sequencing_qc,
    sample_pass_sequencing_qc,
)
from cg.store.models import Case


class QualityCheck(Enum):
    """
    Parent class for the quality checks.
    """


class SequencingQCCheck(QualityCheck):
    CASE_PASSES: Callable = case_pass_sequencing_qc
    SAMPLE_PASSES: Callable = sample_pass_sequencing_qc
    ALL_SAMPLES_IN_CASE_HAVE_READS: Callable = all_samples_in_case_have_reads
    ANY_SAMPLE_IN_CASE_HAS_READS: Callable = any_sample_in_case_has_reads


def get_sequencing_quality_check_for_case(case: Case) -> Callable:
    """Return the appropriate sequencing quality checks for the workflow for a case."""
    workflow: Workflow = case.data_analysis

    workflow_qc_mapping = {
        Workflow.BALSAMIC: SequencingQCCheck.CASE_PASSES,
        Workflow.BALSAMIC_PON: SequencingQCCheck.CASE_PASSES,
        Workflow.BALSAMIC_UMI: SequencingQCCheck.CASE_PASSES,
        Workflow.MIP_DNA: SequencingQCCheck.CASE_PASSES,
        Workflow.MIP_RNA: SequencingQCCheck.CASE_PASSES,
        Workflow.RAREDISEASE: SequencingQCCheck.CASE_PASSES,
        Workflow.RNAFUSION: SequencingQCCheck.CASE_PASSES,
        Workflow.TOMTE: SequencingQCCheck.CASE_PASSES,
        Workflow.FLUFFY: SequencingQCCheck.ANY_SAMPLE_IN_CASE_HAS_READS,
        Workflow.RAW_DATA: SequencingQCCheck.ANY_SAMPLE_IN_CASE_HAS_READS,
        Workflow.MICROSALT: SequencingQCCheck.ANY_SAMPLE_IN_CASE_HAS_READS,
        Workflow.MUTANT: SequencingQCCheck.ANY_SAMPLE_IN_CASE_HAS_READS,
        Workflow.TAXPROFILER: SequencingQCCheck.ALL_SAMPLES_IN_CASE_HAVE_READS,
        Workflow.NALLO: SequencingQCCheck.ALL_SAMPLES_IN_CASE_HAVE_READS,
    }

    if workflow in workflow_qc_mapping:
        return workflow_qc_mapping[workflow]

    raise ValueError(f"Workflow {workflow} does not have a sequencing quality check.")


def get_sample_sequencing_quality_check() -> Callable:
    return SequencingQCCheck.SAMPLE_PASSES


def run_quality_checks(quality_checks: list[QualityCheck], **kwargs) -> bool:
    return all(quality_check(**kwargs) for quality_check in quality_checks)
