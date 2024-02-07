"""Tests for MicroSALT analysis."""

from datetime import datetime
from pathlib import Path

from mock import MagicMock

from cg.apps.lims.api import LimsAPI
from cg.meta.workflow.microsalt import MicrosaltAnalysisAPI
from cg.meta.workflow.microsalt.utils import get_project_directory_date
from cg.models.cg_config import CGConfig
from cg.store.models import Case


def test_get_cases_to_store_pass(
    qc_microsalt_context: CGConfig,
    mocker,
    microsalt_qc_pass_run_dir_path: Path,
    metrics_file_passing_qc: Path,
):
    """Test get cases to store for a microsalt case that passes QC."""

    # GIVEN a store with a QC ready microsalt case that will pass QC
    microsalt_api: MicrosaltAnalysisAPI = qc_microsalt_context.meta_apis["analysis_api"]
    mocker.patch.object(
        MicrosaltAnalysisAPI, "get_metrics_file_path", return_value=metrics_file_passing_qc
    )
    mocker.patch.object(
        MicrosaltAnalysisAPI, "get_case_path", return_value=microsalt_qc_pass_run_dir_path
    )

    # WHEN retrieving cases to store
    cases_to_store: list[Case] = microsalt_api.get_cases_to_store()

    # THEN cases should returned
    assert cases_to_store


def test_get_date_from_project_directory():
    # GIVEN a microsalt analysis run directory name
    run_dir_name = "ACC13796_2024.2.5_15.58.22"

    # WHEN parsing the project directory date
    run_date: datetime = get_project_directory_date(run_dir_name)

    # THEN the date should be parsed correctly
    assert run_date == datetime(2024, 2, 5, 15, 58, 22)
