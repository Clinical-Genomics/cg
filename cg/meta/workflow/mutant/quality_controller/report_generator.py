from pathlib import Path

from cg.io.json import write_json
from cg.meta.workflow.mutant.quality_controller.models import (
    CaseQualityResult,
    SamplesQualityResults,
)
from cg.meta.workflow.mutant.quality_controller.result_logger import samples_results_message


class ReportGenerator:
    @staticmethod
    def write_report(
        out_file: Path,
        case_quality_result: CaseQualityResult,
        samples_quality_results: SamplesQualityResults,
    ) -> None:
        summary: str = ReportGenerator.get_summary(
            case_quality_result=case_quality_result, samples_quality_results=samples_quality_results
        )
        report_content = {
            "summary": summary,
            "case": case_quality_result.model_dump(),
            "samples": samples_quality_results.model_dump(),
        }
        write_json(file_path=out_file, content=report_content)

    @staticmethod
    def get_summary(
        case_quality_result: CaseQualityResult,
        samples_quality_results: SamplesQualityResults,
        report_path: Path | None = None,
    ) -> str:
        case_summary: str = (
            "Case passed QC. " if case_quality_result.passes_qc else "Case failed QC. "
        )
        if report_path and not case_quality_result.passes_qc:
            case_summary += f"See QC report: {report_path}\n "
        sample_summary: str = samples_results_message(
            samples_quality_results=samples_quality_results
        )
        return case_summary + sample_summary
