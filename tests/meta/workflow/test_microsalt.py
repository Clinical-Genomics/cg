"""Tests for MicroSALT analysis."""
from pathlib import Path

from mock import MagicMock
from cg.apps.lims.api import LimsAPI

from cg.meta.workflow.microsalt import MicrosaltAnalysisAPI
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
