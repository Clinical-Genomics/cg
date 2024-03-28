from typing import Callable
from cg.constants.constants import Workflow
from cg.services.pre_analysis_quality_check.sequencing_quality_checks.utils import (
    any_sample_in_case_has_reads,
    express_sample_has_enough_reads,
    get_express_sequencing_qc_of_case,
    get_sequencing_qc_of_case,
    ready_made_library_sample_has_enough_reads,
    sample_has_enough_reads,
)


class WorkflowQualityCheckMapper:
    CASE_SEQUENCING_QUALITY_CHECKS: dict[Workflow, list[Callable]] = {
        Workflow.BALSAMIC: [get_express_sequencing_qc_of_case, get_sequencing_qc_of_case],
        Workflow.BALSAMIC_PON: [get_express_sequencing_qc_of_case, get_sequencing_qc_of_case],
        Workflow.BALSAMIC_QC: [get_express_sequencing_qc_of_case, get_sequencing_qc_of_case],
        Workflow.BALSAMIC_UMI: [get_express_sequencing_qc_of_case, get_sequencing_qc_of_case],
        Workflow.FLUFFY: [any_sample_in_case_has_reads],
        Workflow.FASTQ: [any_sample_in_case_has_reads],
        Workflow.MIP_DNA: [get_express_sequencing_qc_of_case, get_sequencing_qc_of_case],
        Workflow.MIP_RNA: [get_express_sequencing_qc_of_case, get_sequencing_qc_of_case],
        Workflow.RAREDISEASE: [get_express_sequencing_qc_of_case, get_sequencing_qc_of_case],
        Workflow.MICROSALT: [any_sample_in_case_has_reads],
        Workflow.MUTANT: [any_sample_in_case_has_reads],
        Workflow.RNAFUSION: [get_express_sequencing_qc_of_case, get_sequencing_qc_of_case],
        Workflow.TAXPROFILER: [any_sample_in_case_has_reads],
    }

    SAMPLE_SEQUENCING_QUALITY_CHECKS: list[Callable] = [
        ready_made_library_sample_has_enough_reads,
        express_sample_has_enough_reads,
        sample_has_enough_reads,
    ]

    @classmethod
    def get_quality_checks_for_workflow(cls, workflow: Workflow) -> list[Callable]:
        sequencing_quality_checks: list[Callable] | None = cls.CASE_SEQUENCING_QUALITY_CHECKS.get(
            workflow, None
        )
        if not sequencing_quality_checks:
            raise NotImplementedError(
                f"No sequencing quality check have implemented for workflow {workflow}."
            )
        return sequencing_quality_checks

    @classmethod
    def get_sample_quality_checks(cls) -> list[Callable]:
        sample_sequencing_quality_checks: list[Callable] = cls.SAMPLE_SEQUENCING_QUALITY_CHECKS
        return sample_sequencing_quality_checks
