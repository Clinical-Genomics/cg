"""Tests for MicroSALT analysis."""
import logging
from pathlib import Path

from cg.apps.tb.api import TrailblazerAPI

from cg.meta.workflow.microsalt import MicrosaltAnalysisAPI
from cg.meta.workflow.microsalt.quality_controller.report_generator import ReportGenerator
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


def test_get_cases_to_store_pass():
    """Test get cases to store for a microsalt case that passes QC."""
    pass


def test_get_cases_to_store_fail():
    """Test get cases to store for a microsalt case that fails QC."""
    pass
