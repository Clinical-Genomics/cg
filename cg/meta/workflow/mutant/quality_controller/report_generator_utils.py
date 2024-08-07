from pathlib import Path

from cg.io.json import write_json
from cg.meta.workflow.microsalt.constants import QUALITY_REPORT_FILE_NAME
from cg.meta.workflow.mutant.quality_controller.models import (
    CaseQualityResult,
    SamplesQualityResults,
)
from cg.meta.workflow.mutant.quality_controller.result_logger_utils import samples_results_message


def get_report_path(case_path: Path) -> Path:
    return case_path.joinpath(QUALITY_REPORT_FILE_NAME)


def write_report(
    case_path: Path,
    case_quality_result: CaseQualityResult,
    samples_quality_results: SamplesQualityResults,
) -> None:
    report_file_path: Path = get_report_path(case_path=case_path)

    summary: str = get_summary(
        case_quality_result=case_quality_result,
        samples_quality_results=samples_quality_results,
        report_file_path=report_file_path,
    )
    report_content = {
        "summary": summary,
        "case": case_quality_result.model_dump(),
        "samples": samples_quality_results.model_dump(),
    }

    write_json(file_path=report_file_path, content=report_content)


def get_summary(
    case_quality_result: CaseQualityResult,
    samples_quality_results: SamplesQualityResults,
    report_file_path: Path,
) -> str:
    case_summary: str = "Case passed QC. " if case_quality_result.passes_qc else "Case failed QC. "
    sample_summary: str = samples_results_message(samples_quality_results=samples_quality_results)
    summary = case_summary + sample_summary
    if not case_quality_result.passes_qc:
        summary += f" QC report: {report_file_path}"
    return summary
