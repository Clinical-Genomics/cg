from typing import Callable

from cg.constants.constants import Pipeline
from cg.meta.workflow.pre_analysis_quality_check.sequencing_quality_metrics.utils import (
    any_sample_in_case_has_reads,
    get_express_sequencing_qc_of_case,
    get_sequencing_qc_of_case,
)

SEQUENCING_QUALITY_CHECKS: dict[Pipeline, list[Callable]] = {
    Pipeline.BALSAMIC: [get_express_sequencing_qc_of_case, get_sequencing_qc_of_case],
    Pipeline.BALSAMIC_PON: [get_express_sequencing_qc_of_case, get_sequencing_qc_of_case],
    Pipeline.BALSAMIC_QC: [get_express_sequencing_qc_of_case, get_sequencing_qc_of_case],
    Pipeline.BALSAMIC_UMI: [get_express_sequencing_qc_of_case, get_sequencing_qc_of_case],
    Pipeline.FLUFFY: [any_sample_in_case_has_reads],
    Pipeline.MIP_DNA: [get_express_sequencing_qc_of_case, get_sequencing_qc_of_case],
    Pipeline.MIP_RNA: [get_express_sequencing_qc_of_case, get_sequencing_qc_of_case],
    Pipeline.RAREDISEASE: [get_express_sequencing_qc_of_case, get_sequencing_qc_of_case],
    Pipeline.MICROSALT: [any_sample_in_case_has_reads],
    Pipeline.SARS_COV_2: [any_sample_in_case_has_reads],
    Pipeline.RNAFUSION: [get_express_sequencing_qc_of_case, get_sequencing_qc_of_case],
    Pipeline.TAXPROFILER: [any_sample_in_case_has_reads],
}
