"""Tests for MicroSALT analysis."""
from pathlib import Path

from mock import MagicMock
from cg.apps.lims.api import LimsAPI

from cg.meta.workflow.microsalt import MicrosaltAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store.models import Case


def test_get_latest_case_path(
    mocker,
    qc_microsalt_context: CGConfig,
    microsalt_case_qc_pass: str,
    microsalt_analysis_dir: Path,
):
    """Test get_latest_case_path return the first case path and not single sample path"""
    microsalt_api: MicrosaltAnalysisAPI = qc_microsalt_context.meta_apis["analysis_api"]

    # GIVEN a case with different case paths, both single sample and case analyses
    mocker.patch.object(MicrosaltAnalysisAPI, "get_project", return_value="ACC12345")
    mocker.patch.object(
        MicrosaltAnalysisAPI,
        "get_case_path",
        return_value=[
            Path(microsalt_analysis_dir, "ACC12345A2_2023"),
            Path(microsalt_analysis_dir, "ACC12345_2022"),
            Path(microsalt_analysis_dir, "ACC12345A1_2023"),
        ],
    )
    # WHEN getting the latest case path
    path = microsalt_api.get_latest_case_path(case_id=microsalt_case_qc_pass)

    # THEN the first case path should be returned
    assert Path(microsalt_analysis_dir, "ACC12345_2022") == path


def test_get_cases_to_store_pass(
    qc_microsalt_context: CGConfig,
    mocker,
    microsalt_qc_pass_lims_project: str,
    microsalt_qc_pass_run_dir_path: Path,
):
    """Test get cases to store for a microsalt case that passes QC."""

    # GIVEN a store with a QC ready microsalt case that will pass QC
    microsalt_api: MicrosaltAnalysisAPI = qc_microsalt_context.meta_apis["analysis_api"]
    mocker.patch.object(LimsAPI, "get_sample_project", return_value=microsalt_qc_pass_lims_project)
    mocker.patch.object(
        MicrosaltAnalysisAPI, "get_latest_case_path", return_value=microsalt_qc_pass_run_dir_path
    )

    # WHEN retrieving cases to store
    cases_to_store: list[Case] = microsalt_api.get_cases_to_store()

    # THEN cases should returned
    assert cases_to_store
