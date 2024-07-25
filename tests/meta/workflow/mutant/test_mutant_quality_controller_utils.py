from cg.meta.workflow.mutant.quality_controller.models import SampleQualityResults
from cg.meta.workflow.mutant.quality_controller.utils import (
    internal_negative_control_qc_pass,
    external_negative_control_qc_pass,
)


def test_internal_negative_control_qc_pass(
    sample_results_case_qc_pass: list[SampleQualityResults],
) -> bool:
    # GIVEN a sample_results object where the internal_negative_control passes qc

    # WHEN performing qc on the sample
    internal_negative_control_pass_qc: bool = internal_negative_control_qc_pass(
        sample_results_case_qc_pass
    )

    # THEN internal_negative_control_pass_qc=True

    assert internal_negative_control_pass_qc is True


def test_external_negative_control_qc_pass(
    sample_results_case_qc_pass: list[SampleQualityResults],
) -> bool:
    # GIVEN a sample_results object where the external_negative_control passes qc

    # WHEN performing qc on the sample
    external_negative_control_pass_qc: bool = external_negative_control_qc_pass(
        sample_results_case_qc_pass
    )

    # THEN external_negative_control_pass_qc=True

    assert external_negative_control_pass_qc is True
