from pathlib import Path
from cg.io.json import write_json
from cg.meta.workflow.mutant.quality_controller.models import (
    CaseQualityResult,
    MutantReport,
    SamplesQualityResults,
)
from cg.meta.workflow.mutant.quality_controller.result_logger_utils import (
    get_samples_results_message,
)


def write_report(
    case_qc_report_path: Path,
    case_quality_result: CaseQualityResult,
    samples_quality_results: SamplesQualityResults,
) -> None:
    summary: str = get_summary(
        case_quality_result=case_quality_result,
        samples_quality_results=samples_quality_results,
    )
    report = MutantReport(
        summary=summary,
        case=case_quality_result.model_dump(),
        samples=samples_quality_results.model_dump(),
    )

    write_json(file_path=case_qc_report_path, content=report.model_dump())


def get_summary(
    case_quality_result: CaseQualityResult,
    samples_quality_results: SamplesQualityResults,
) -> str:
    case_summary: str = "Case passed QC. " if case_quality_result.passes_qc else "Case failed QC. "
    sample_summary: str = get_samples_results_message(
        samples_quality_results=samples_quality_results
    )
    summary = case_summary + sample_summary
    return summary
