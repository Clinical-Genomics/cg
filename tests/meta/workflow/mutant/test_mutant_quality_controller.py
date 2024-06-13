from cg.meta.workflow.mutant.quality_controller.models import SampleQualityResult


def test_quality_control(mutant_case_qc_pass, quality_controller, passing_report_path):
    # GIVEN a case object and a corresponding case_results_file_path

    # WHEN performing qc

    quality_controller.quality_control(
        case=mutant_case_qc_pass,
        case_path="",
        case_results_file_path=passing_report_path,
    )

    # THEN no error is thrown


def test_quality_control_samples(quality_controller, quality_metrics_case_qc_pass):
    # GIVEN a case object

    # WHEN performing qc on samples
    list_sample_quality_result = quality_controller.quality_control_samples(
        quality_metrics=quality_metrics_case_qc_pass
    )

    # THEN no error is thrown
    assert isinstance(list_sample_quality_result, list)
    assert isinstance(list_sample_quality_result[0], SampleQualityResult)


def test_quality_control_case(quality_controller, sample_results_case_qc_pass):
    # GIVEN a case object and a corresponding case_results_file_path

    # WHEN performing qc

    quality_controller.quality_control_case(sample_results=sample_results_case_qc_pass)

    # THEN no error is thrown


def test_case_qc_pass(quality_controller, sample_results_case_qc_pass):
    # GIVEN a case object and a corresponding case_results_file_path

    # WHEN performing qc

    quality_controller.case_qc_pass(sample_results=sample_results_case_qc_pass)

    # THEN no error is thrown
