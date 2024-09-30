from pathlib import Path

import pytest
from dateutil.parser import parse

from cg.constants import Workflow
from cg.meta.workflow.rnafusion import RnafusionAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store.models import Analysis


@pytest.mark.parametrize(
    "before_date, should_be_cleaned", [("2024-12-31", False), ("2024-01-01", True)]
)
def test_clean_case_directories(
    tmp_path: Path, before_date: str, should_be_cleaned: bool, rnafusion_context: CGConfig
):
    """Tests cleaning of case directories."""

    # GIVEN a file which was modified days_since_modification ago
    analysis_to_clean: Analysis = rnafusion_context.status_db.add_analysis(
        workflow=Workflow.RNAFUSION, started_at=parse(before_date)
    )
    analysis_to_clean.case = rnafusion_context.status_db.get_cases()[0]

    # GIVEN an NF Tower analysis API
    analysis_api: RnafusionAnalysisAPI = rnafusion_context.meta_apis["analysis_api"]

    case_path = analysis_api.get_case_path(analysis_to_clean.case.internal_id)
    file_path = Path(case_path, "test_file")
    file_path.touch()

    # WHEN cleaning the tmp_path/cases directory of old files
    analysis_api.clean_past_run_dirs(before_date=before_date, skip_confirmation=True)

    # THEN the file should be deleted if it was old.
    assert file_path.exists() != should_be_cleaned
