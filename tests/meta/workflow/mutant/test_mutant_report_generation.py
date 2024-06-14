from pathlib import Path
from cg.meta.workflow.mutant.quality_controller.models import CaseQualityResult, SampleQualityResult
from cg.meta.workflow.mutant.quality_controller.report_generator import ReportGenerator


def test_report_generation(
    mutant_qc_report_path_case_qc_pass: Path,
    case_quality_result_qc_pass: CaseQualityResult,
    sample_results_case_qc_pass: list[SampleQualityResult],
):
    # GIVEN a report path, case, sample_results
    # WHEN generating a qc_report_file
    ReportGenerator.report(
        out_file=mutant_qc_report_path_case_qc_pass,
        case=case_quality_result_qc_pass,
        samples=sample_results_case_qc_pass,
    )
    # THEN no errors are thrown
