from pathlib import Path

import pytest
from dateutil.parser import parse

from cg.constants import Workflow
from cg.meta.workflow.rnafusion import RnafusionAnalysisAPI
from cg.meta.workflow.taxprofiler import TaxprofilerAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store.models import Analysis


@pytest.mark.parametrize(
    "before_date, should_be_cleaned", [("2024-12-31", True), ("2024-01-01", False)]
)
def test_clean_rnafusion_case_directories(
    before_date: str, should_be_cleaned: bool, rnafusion_context: CGConfig
):
    """Tests cleaning of case directories."""

    # GIVEN a file which was modified days_since_modification ago
    analysis_to_clean: Analysis = rnafusion_context.status_db.add_analysis(
        workflow=Workflow.RNAFUSION, started_at=parse("2024-06-06"), uploaded=parse("2024-06-06")
    )
    analysis_to_clean.case = rnafusion_context.status_db.get_cases()[0]
    rnafusion_context.status_db.session.add(analysis_to_clean)
    rnafusion_context.status_db.commit_to_store()

    # GIVEN an RNAFusion analysis API
    analysis_api: RnafusionAnalysisAPI = rnafusion_context.meta_apis["analysis_api"]

    case_path = analysis_api.get_case_path(analysis_to_clean.case.internal_id)
    case_path.mkdir()
    file_path = Path(case_path, "test_file")
    file_path.touch()

    # WHEN cleaning the tmp_path/cases directory of old files
    analysis_api.clean_past_run_dirs(before_date=before_date, skip_confirmation=True)

    # THEN the file should be deleted if it was old.
    assert file_path.exists() != should_be_cleaned


@pytest.mark.parametrize(
    "before_date, should_be_cleaned", [("2024-12-31", True), ("2024-01-01", False)]
)
def test_clean_taxprofiler_case_directories(
    before_date: str, should_be_cleaned: bool, taxprofiler_context: CGConfig
):
    """Tests cleaning of case directories."""

    # GIVEN a file which was modified days_since_modification ago
    analysis_to_clean: Analysis = taxprofiler_context.status_db.add_analysis(
        workflow=Workflow.TAXPROFILER, started_at=parse("2024-06-06"), uploaded=parse("2024-06-06")
    )
    analysis_to_clean.case = taxprofiler_context.status_db.get_cases()[0]
    taxprofiler_context.status_db.session.add(analysis_to_clean)
    taxprofiler_context.status_db.commit_to_store()

    # GIVEN a Taxprofiler analysis API
    analysis_api: TaxprofilerAnalysisAPI = taxprofiler_context.meta_apis["analysis_api"]

    case_path = analysis_api.get_case_path(analysis_to_clean.case.internal_id)
    case_path.mkdir()
    file_path = Path(case_path, "test_file")
    file_path.touch()

    # WHEN cleaning the tmp_path/cases directory of old files
    analysis_api.clean_past_run_dirs(before_date=before_date, skip_confirmation=True)

    # THEN the file should be deleted if it was old.
    assert file_path.exists() != should_be_cleaned
