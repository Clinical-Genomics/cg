from pathlib import Path
from cg.meta.workflow.mutant.quality_controller.models import (
    QualityMetrics,
    QualityResult,
    SampleQualityResults,
)
from cg.meta.workflow.mutant.quality_controller.quality_controller import QualityController
from cg.store.models import Case, Sample


def test_quality_control_case_qc_pass(
    case_qc_pass: Case,
    quality_controller: QualityController,
    mutant_analysis_dir_case_qc_pass: Path,
    mutant_results_file_path_qc_pass: Path,
):
    # GIVEN a case object and a corresponding case_results_file_path

    # WHEN performing qc

    case_qc: QualityResult = quality_controller.quality_control(
        case=case_qc_pass,
        case_path=mutant_analysis_dir_case_qc_pass,
        case_results_file_path=mutant_results_file_path_qc_pass,
    )

    # THEN no error is thrown
    assert case_qc.case.internal_negative_control_passes_qc is True
    assert case_qc.case.external_negative_control_passes_qc is True
    assert case_qc.passes_qc is True


def test_quality_control_case_qc_fail(
    case_qc_fail: Case,
    quality_controller: QualityController,
    mutant_analysis_dir_case_qc_fail: Path,
    mutant_results_file_path_qc_fail: Path,
):
    # GIVEN a case object and a corresponding case_results_file_path

    # WHEN performing qc

    quality_controller.quality_control(
        case=case_qc_fail,
        case_path=mutant_analysis_dir_case_qc_fail,
        case_results_file_path=mutant_results_file_path_qc_fail,
    )

    # THEN no error is thrown


def test_quality_control_case_qc_fail_with_failing_controls(
    case_qc_fail_with_failing_controls: Case,
    quality_controller: QualityController,
    mutant_analysis_dir_case_qc_fail_with_failing_controls: Path,
    mutant_results_file_path_qc_fail_with_failing_controls: Path,
):
    # GIVEN a case object and a corresponding case_results_file_path

    # WHEN performing qc

    case_qc: QualityResult = quality_controller.quality_control(
        case=case_qc_fail_with_failing_controls,
        case_path=mutant_analysis_dir_case_qc_fail_with_failing_controls,
        case_results_file_path=mutant_results_file_path_qc_fail_with_failing_controls,
    )

    # THEN no error is thrown
    assert case_qc.case.internal_negative_control_passes_qc is False
    assert case_qc.case.external_negative_control_passes_qc is False
    assert case_qc.passes_qc is False


def test_quality_control_samples(
    quality_controller: QualityController, quality_metrics_case_qc_pass: QualityMetrics
):
    # GIVEN a case object

    # WHEN performing qc on samples
    list_sample_quality_result = quality_controller.quality_control_samples(
        quality_metrics=quality_metrics_case_qc_pass
    )

    # THEN no error is thrown
    assert isinstance(list_sample_quality_result, list)
    assert isinstance(list_sample_quality_result[0], SampleQualityResults)


def test_quality_control_sample_pass_qc(
    quality_controller: QualityController,
    sample_qc_pass: Sample,
    quality_metrics_case_qc_pass: QualityMetrics,
):
    # GIVEN a sample that passes qc and a quality_metrics object for a case containing the sample
    # WHEN performing qc on the sample
    sample_quality_result: SampleQualityResults = quality_controller.quality_control_sample(
        sample_id=sample_qc_pass.internal_id, quality_metrics=quality_metrics_case_qc_pass
    )

    # THEM the result is pass_qc=True
    assert sample_quality_result.passes_qc is True


def test_quality_control_sample_fail_qc(
    quality_controller: QualityController,
    sample_qc_fail: Sample,
    quality_metrics_case_qc_fail: QualityMetrics,
):
    # GIVEN a sample that fails qc and a quality_metrics object for a case containing the sample

    # WHEN performing qc on the sample
    sample_quality_result: SampleQualityResults = quality_controller.quality_control_sample(
        sample_id=sample_qc_fail.internal_id, quality_metrics=quality_metrics_case_qc_fail
    )

    # THEM the result is pass_qc=False
    assert sample_quality_result.passes_qc is False


def test_quality_control_case(
    quality_controller: QualityController, sample_results_case_qc_pass: list[SampleQualityResults]
):
    # GIVEN a case object and a corresponding case_results_file_path

    # WHEN performing qc

    quality_controller.quality_control_case(sample_results=sample_results_case_qc_pass)

    # THEN no error is thrown


def test_case_qc_pass(
    quality_controller: QualityController, sample_results_case_qc_pass: list[SampleQualityResults]
):
    # GIVEN a case object and a corresponding case_results_file_path

    # WHEN performing qc

    case_pass_qc = quality_controller.case_qc_pass(sample_results=sample_results_case_qc_pass)

    # THEN no error is thrown

    assert case_pass_qc is True
