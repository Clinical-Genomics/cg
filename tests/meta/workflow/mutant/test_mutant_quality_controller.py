from pathlib import Path
from cg.meta.workflow.mutant.quality_controller.models import QualityResult, SampleQualityResult


def test_quality_control_case_qc_pass(case_qc_pass, quality_controller, report_path_qc_pass):
    # GIVEN a case object and a corresponding case_results_file_path

    # WHEN performing qc

    case_qc: QualityResult = quality_controller.quality_control(
        case=case_qc_pass,
        case_path=Path(""),
        case_results_file_path=report_path_qc_pass,
    )

    # THEN no error is thrown
    assert case_qc.case.internal_negative_control_passes_qc is True
    assert case_qc.case.external_negative_control_passes_qc is True
    assert case_qc.passes_qc is True


def test_quality_control_case_qc_fail(case_qc_fail, quality_controller, report_path_qc_fail):
    # GIVEN a case object and a corresponding case_results_file_path

    # WHEN performing qc

    quality_controller.quality_control(
        case=case_qc_fail,
        case_path=Path(""),
        case_results_file_path=report_path_qc_fail,
    )

    # THEN no error is thrown


def test_quality_control_case_qc_fail_with_failing_controls(
    case_qc_fail_with_failing_controls,
    quality_controller,
    report_path_qc_fail_with_failing_controls,
):
    # GIVEN a case object and a corresponding case_results_file_path

    # WHEN performing qc

    case_qc: QualityResult = quality_controller.quality_control(
        case=case_qc_fail_with_failing_controls,
        case_path=Path(""),
        case_results_file_path=report_path_qc_fail_with_failing_controls,
    )

    # THEN no error is thrown
    assert case_qc.case.internal_negative_control_passes_qc is False
    assert case_qc.case.external_negative_control_passes_qc is False
    assert case_qc.passes_qc is False


def test_quality_control_samples(quality_controller, quality_metrics_case_qc_pass):
    # GIVEN a case object

    # WHEN performing qc on samples
    list_sample_quality_result = quality_controller.quality_control_samples(
        quality_metrics=quality_metrics_case_qc_pass
    )

    # THEN no error is thrown
    assert isinstance(list_sample_quality_result, list)
    assert isinstance(list_sample_quality_result[0], SampleQualityResult)


def test_quality_control_sample_pass_qc(
    quality_controller, sample_qc_pass, quality_metrics_case_qc_pass
):
    # GIVEN a sample that passes qc and a quality_metrics object for a case containing the sample
    # WHEN performing qc on the sample
    sample_quality_result: SampleQualityResult = quality_controller.quality_control_sample(
        sample_id=sample_qc_pass.internal_id, quality_metrics=quality_metrics_case_qc_pass
    )

    # THEM the result is pass_qc=True
    assert sample_quality_result.passes_qc is True


def test_quality_control_sample_fail_qc(
    quality_controller, sample_qc_fail, quality_metrics_case_qc_fail
):
    # GIVEN a sample that fails qc and a quality_metrics object for a case containing the sample

    # WHEN performing qc on the sample
    sample_quality_result: SampleQualityResult = quality_controller.quality_control_sample(
        sample_id=sample_qc_fail.internal_id, quality_metrics=quality_metrics_case_qc_fail
    )

    # THEM the result is pass_qc=False
    assert sample_quality_result.passes_qc is False


def test_quality_control_case(quality_controller, sample_results_case_qc_pass):
    # GIVEN a case object and a corresponding case_results_file_path

    # WHEN performing qc

    quality_controller.quality_control_case(sample_results=sample_results_case_qc_pass)

    # THEN no error is thrown


def test_case_qc_pass(quality_controller, sample_results_case_qc_pass):
    # GIVEN a case object and a corresponding case_results_file_path

    # WHEN performing qc

    case_pass_qc = quality_controller.case_qc_pass(sample_results=sample_results_case_qc_pass)

    # THEN no error is thrown

    assert case_pass_qc is True
