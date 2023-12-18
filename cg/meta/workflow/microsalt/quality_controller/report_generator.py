from pathlib import Path
from typing import List

from cg.io.json import write_json
from cg.meta.workflow.microsalt.quality_controller.models import (
    CaseQualityResult,
    SampleQualityResult,
)


class ReportGenerator:
    @staticmethod
    def report(out_file: Path, case: CaseQualityResult, samples: List[SampleQualityResult]) -> None:
        report_content = {
            "case": case.model_dump(),
            "samples": [sample.model_dump() for sample in samples],
        }
        write_json(file_path=out_file, content=report_content)
