from pathlib import Path
from typing import List

from cg.io.json import write_json
from cg.meta.workflow.microsalt.quality_controller.models import (
    CaseQualityResult,
    SampleQualityResult,
)
from cg.meta.workflow.microsalt.quality_controller.result_logger import sample_result_message


class ReportGenerator:
    @staticmethod
    def report(out_file: Path, case: CaseQualityResult, samples: List[SampleQualityResult]) -> None:
        summary: str = ReportGenerator.get_summary(case=case, samples=samples)
        report_content = {
            "summary": summary,
            "case": case.model_dump(),
            "samples": [sample.model_dump() for sample in samples],
        }
        write_json(file_path=out_file, content=report_content)

    @staticmethod
    def get_summary(case: CaseQualityResult, samples: List[SampleQualityResult]) -> str:
        case_summary: str = "Case passed QC. " if case.passes_qc else "Case failed QC. "
        sample_summary: str = sample_result_message(samples)
        return case_summary + sample_summary
