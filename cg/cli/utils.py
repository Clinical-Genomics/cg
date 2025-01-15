import re
import shutil

import rich_click as click

from cg.constants import Workflow
from cg.meta.workflow.raredisease import RarediseaseAnalysisAPI
from cg.meta.workflow.rnafusion import RnafusionAnalysisAPI
from cg.meta.workflow.taxprofiler import TaxprofilerAnalysisAPI
from cg.meta.workflow.tomte import TomteAnalysisAPI


def echo_lines(lines: list[str]) -> None:
    for line in lines:
        click.echo(line)


def is_case_name_allowed(name: str) -> bool:
    """Returns true if the given name consists only of letters, numbers and dashes."""
    allowed_pattern: re.Pattern = re.compile("^[A-Za-z0-9-]+$")
    return bool(allowed_pattern.fullmatch(name))


CLICK_CONTEXT_SETTINGS: dict[str, int] = {
    "max_content_width": shutil.get_terminal_size().columns - 10
}


TOWER_WORKFLOW_TO_ANALYSIS_API_MAP: dict = {
    Workflow.RAREDISEASE: RarediseaseAnalysisAPI,
    Workflow.RNAFUSION: RnafusionAnalysisAPI,
    Workflow.TAXPROFILER: TaxprofilerAnalysisAPI,
    Workflow.TOMTE: TomteAnalysisAPI,
}
