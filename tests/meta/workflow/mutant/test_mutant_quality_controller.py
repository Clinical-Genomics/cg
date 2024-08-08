from pathlib import Path
from cg.meta.workflow.mutant.quality_controller.models import (
    QualityResult,
    CaseQualityResult,
    QualityMetrics,
    SampleQualityResults,
    SampleResults,
    SamplesQualityResults,
)
from cg.meta.workflow.mutant.quality_controller.quality_controller import (
    MutantQualityController,
)
from cg.store.models import Case, Sample


def test__get_sample_quality_results(
    mutant_quality_controller: MutantQualityController,
    sample_qc_pass: Sample,
    mutant_sample_results_sample_qc_pass: SampleResults,
):
    # GIVEN a sample that passes qc and its corresponding SampleResults

    # WHEN peforming quality control on the sample
    sample_quality_results_sample_qc_pass: (
        SampleQualityResults
    ) = mutant_quality_controller._get_sample_quality_results(
        sample=sample_qc_pass,
        sample_results=mutant_sample_results_sample_qc_pass,
    )
    # THEN the sample passes qc
    assert sample_quality_results_sample_qc_pass.passes_qc is True


def test__get_samples_quality_results(
    mutant_quality_controller: MutantQualityController,
    mutant_quality_metrics_qc_pass: QualityMetrics,
):
    # GIVEN a quality metrics objrect from a case where all samples pass QC

    # WHEN performing quality control on all the samples
    samples_quality_results: (
        SamplesQualityResults
    ) = mutant_quality_controller._get_samples_quality_results(
        quality_metrics=mutant_quality_metrics_qc_pass
    )

    # THEN no error is raised and the correct quality results are generated
    assert samples_quality_results.internal_negative_control.passes_qc is True
    assert samples_quality_results.external_negative_control.passes_qc is True
    assert len(samples_quality_results.samples) == 1
    assert all(samples_quality_results.samples) is True


def test__get_case_quality_result(
    mutant_quality_controller: MutantQualityController,
    samples_quality_results_case_qc_pass: SamplesQualityResults,
):
    # GIVEN a samples_quality_results object for a case that passes QC

    # WHEN performing QC on the case
    case_quality_result: CaseQualityResult = mutant_quality_controller._get_case_quality_result(
        samples_quality_results=samples_quality_results_case_qc_pass
    )

    # THEN the correct result is generated
    assert case_quality_result.passes_qc is True
    assert case_quality_result.internal_negative_control_passes_qc is True
    assert case_quality_result.external_negative_control_passes_qc is True


def test_get_quality_control_result_case_qc_pass(
    mutant_quality_controller: MutantQualityController,
    mutant_case_qc_pass: Case,
    mutant_results_file_path_case_qc_pass: Path,
    mutant_qc_report_path_case_qc_pass: Path,
):
    # GIVEN a case that passes QC

    # WHEN performing QC on the case

    case_quality_result: QualityResult = mutant_quality_controller.get_quality_control_result(
        case=mutant_case_qc_pass,
        case_results_file_path=mutant_results_file_path_case_qc_pass,
        case_qc_report_path=mutant_qc_report_path_case_qc_pass,
    )

    # THEN the case passes qc
    assert case_quality_result.passes_qc is True
    assert case_quality_result.case_quality_result.external_negative_control_passes_qc is True
    assert case_quality_result.case_quality_result.internal_negative_control_passes_qc is True


def test_get_quality_control_result_case_qc_fail(
    mutant_quality_controller: MutantQualityController,
    mutant_case_qc_fail: Case,
    mutant_results_file_path_qc_fail: Path,
    mutant_qc_report_path_case_qc_fail: Path,
):
    # GIVEN a case that passes QC

    # WHEN performing QC on the case

    case_quality_result: QualityResult = mutant_quality_controller.get_quality_control_result(
        case=mutant_case_qc_fail,
        case_results_file_path=mutant_results_file_path_qc_fail,
        case_qc_report_path=mutant_qc_report_path_case_qc_fail,
    )

    # THEN the case passes qc
    assert case_quality_result.passes_qc is False
    assert case_quality_result.case_quality_result.external_negative_control_passes_qc is True
    assert case_quality_result.case_quality_result.internal_negative_control_passes_qc is True


def test_get_quality_control_result_case_qc_fail_with_failing_controls(
    mutant_quality_controller: MutantQualityController,
    mutant_case_qc_fail_with_failing_controls: Case,
    mutant_results_file_path_qc_fail_with_failing_controls: Path,
    mutant_qc_report_path_case_qc_fail_with_failing_controls: Path,
):
    # GIVEN a case that does not passe QC due to failing control samples

    # WHEN performing QC on the case

    case_quality_result: QualityResult = mutant_quality_controller.get_quality_control_result(
        case=mutant_case_qc_fail_with_failing_controls,
        case_results_file_path=mutant_results_file_path_qc_fail_with_failing_controls,
        case_qc_report_path=mutant_qc_report_path_case_qc_fail_with_failing_controls,
    )

    # THEN the case does not pass QC and the correct result is retrieved for the control samples
    assert case_quality_result.passes_qc is False
    assert case_quality_result.case_quality_result.external_negative_control_passes_qc is False
    assert case_quality_result.case_quality_result.internal_negative_control_passes_qc is False
