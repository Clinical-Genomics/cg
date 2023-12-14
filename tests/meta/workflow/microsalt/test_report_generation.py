from pathlib import Path

from cg.meta.workflow.microsalt.quality_controller.models import QualityResult
from cg.meta.workflow.microsalt.quality_controller.report_generator import ReportGenerator


def test_generate_report_with_results(quality_results: list[QualityResult], tmp_path: Path):
    # GIVEN quality results

    # GIVEN a file path to write them to
    out_file = Path(tmp_path, "QC_done.json")

    # WHEN generating a report
    ReportGenerator.report(out_file=out_file, sample_results=quality_results)

    # THEN the report is created
    assert out_file.exists()

    # THEN the report is populated
    assert out_file.read_text()
