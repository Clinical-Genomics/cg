"""Tests for MicroSALT analysis."""
import logging
from pathlib import Path

import mock

from cg.constants.constants import CaseActions, Pipeline
from cg.meta.workflow.microsalt import MicrosaltAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.models.orders.sample_base import ControlEnum
from cg.store import Store
from cg.store.models import Case
from tests.mocks.tb_mock import MockTB
from tests.store_helpers import StoreHelpers


def test_qc_check_fail(
    qc_microsalt_context: CGConfig,
    microsalt_qc_fail_run_dir_path: Path,
    microsalt_qc_fail_lims_project: str,
    microsalt_case_qc_fail: str,
    caplog,
    mocker,
):
    """QC check for a microsalt case that should fail."""
    caplog.set_level(logging.INFO)
    store: Store = qc_microsalt_context.status_db
    microsalt_api: MicrosaltAnalysisAPI = qc_microsalt_context.meta_apis["analysis_api"]

    # GIVEN a case that is to be stored
    microsalt_case: Case = store.get_case_by_internal_id(internal_id=microsalt_case_qc_fail)
    for index in range(4):
        microsalt_case.samples[index].reads = 1000

    mocker.patch.object(MicrosaltAnalysisAPI, "create_qc_done_file")

    # WHEN performing QC check
    qc_pass: bool = microsalt_api.microsalt_qc(
        case_id=microsalt_case_qc_fail,
        run_dir_path=microsalt_qc_fail_run_dir_path,
        lims_project=microsalt_qc_fail_lims_project,
    )

    # THEN the QC should fail
    assert not qc_pass
    assert "failed" in caplog.text


def test_qc_check_pass(
    qc_microsalt_context: CGConfig,
    microsalt_qc_pass_run_dir_path: Path,
    microsalt_qc_pass_lims_project: str,
    microsalt_case_qc_pass: str,
    caplog,
    mocker,
):
    """QC check for a microsalt case that should pass."""
    caplog.set_level(logging.INFO)
    store: Store = qc_microsalt_context.status_db
    microsalt_api: MicrosaltAnalysisAPI = qc_microsalt_context.meta_apis["analysis_api"]

    # GIVEN a case that is to be stored
    microsalt_case: Case = store.get_case_by_internal_id(internal_id=microsalt_case_qc_pass)
    microsalt_case.samples[1].control = ControlEnum.negative
    microsalt_case.samples[1].reads = 1100000

    mocker.patch.object(MicrosaltAnalysisAPI, "create_qc_done_file")

    # WHEN performing QC check
    qc_pass: bool = microsalt_api.microsalt_qc(
        case_id=microsalt_case_qc_pass,
        run_dir_path=microsalt_qc_pass_run_dir_path,
        lims_project=microsalt_qc_pass_lims_project,
    )

    # THEN the QC should pass
    assert qc_pass
    assert "passed" in caplog.text


def test_qc_check_negative_control_fail(
    qc_microsalt_context: CGConfig,
    microsalt_qc_fail_run_dir_path: Path,
    microsalt_qc_fail_lims_project: str,
    microsalt_case_qc_fail: str,
    caplog,
    mocker,
):
    """QC check for a microsalt case where a negative control fails QC."""

    caplog.set_level(logging.INFO)
    store = qc_microsalt_context.status_db
    microsalt_api: MicrosaltAnalysisAPI = qc_microsalt_context.meta_apis["analysis_api"]

    # GIVEN a case that is to be stored
    microsalt_case: Case = store.get_case_by_internal_id(internal_id=microsalt_case_qc_fail)
    microsalt_case.samples[0].control = ControlEnum.negative

    mocker.patch.object(MicrosaltAnalysisAPI, "create_qc_done_file")

    # WHEN performing QC check
    qc_pass: bool = microsalt_api.microsalt_qc(
        case_id=microsalt_case_qc_fail,
        run_dir_path=microsalt_qc_fail_run_dir_path,
        lims_project=microsalt_qc_fail_lims_project,
    )

    # THEN the QC should fail
    assert not qc_pass
    assert "failed" in caplog.text
    assert "Negative control sample" in caplog.text


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


def test_get_cases_to_store(
    qc_microsalt_context: CGConfig, helpers: StoreHelpers, trailblazer_api: MockTB
):
    """Test that the cases fetched are Microsalt and finished successfully."""
    # GIVEN a MicrosaltAPI, a Store and a TrailblazerAPI
    analysis_api: MicrosaltAnalysisAPI = qc_microsalt_context.meta_apis["analysis_api"]
    store: Store = analysis_api.status_db
    mock.patch.object(trailblazer_api, "is_latest_analysis_completed", return_value=True)
    analysis_api.trailblazer_api = trailblazer_api

    # GIVEN a running case in the store
    helpers.ensure_case(store=store, data_analysis=Pipeline.MICROSALT, action=CaseActions.RUNNING)

    # WHEN getting the cases to store in Housekeeper
    cases_to_store: list[Case] = analysis_api.get_cases_to_store()
    case: Case = cases_to_store[0]

    # THEN a list with one microsalt case is returned
    assert len(cases_to_store) == 1
    assert case.data_analysis == Pipeline.MICROSALT
    assert case.action == CaseActions.RUNNING
