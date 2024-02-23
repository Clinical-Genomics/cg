from pathlib import Path
from cg.meta.workflow.microsalt.constants import QUALITY_REPORT_FILE_NAME

from cg.meta.workflow.microsalt.quality_controller.models import (
    CaseQualityResult,
    SampleQualityResult,
)
from cg.meta.workflow.microsalt.quality_controller.report_generator import ReportGenerator


def test_generate_report_with_results(
    quality_results: list[SampleQualityResult], case_result: CaseQualityResult, tmp_path: Path
):
    # GIVEN quality results

    # GIVEN a file path to write them to
    out_file = Path(tmp_path, QUALITY_REPORT_FILE_NAME)

    # WHEN generating a report
    ReportGenerator.report(out_file=out_file, samples=quality_results, case=case_result)

    # THEN the report is created
    assert out_file.exists()

    # THEN the report is populated
    assert out_file.read_text()
