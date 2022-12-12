"""Tests for MicroSALT analysis."""
from cg.meta.workflow.microsalt import MicrosaltAnalysisAPI
from cg.models.cg_config import CGConfig
from pathlib import Path
import logging


from cg.store.models import Family


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
    store = qc_microsalt_context.status_db
    microsalt_api: MicrosaltAnalysisAPI = qc_microsalt_context.meta_apis["analysis_api"]

    # GIVEN a case that is to be stored
    microsalt_case: Family = store.family(microsalt_case_qc_fail)
    microsalt_case.samples[0].reads = 1000
    microsalt_case.samples[1].reads = 1000
    microsalt_case.samples[2].reads = 1000
    microsalt_case.samples[3].reads = 1000

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
    assert "Passed Reads Guaranteed = False" in caplog.text
    assert "Passed BP > 10X = False" in caplog.text


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
    store = qc_microsalt_context.status_db
    microsalt_api: MicrosaltAnalysisAPI = qc_microsalt_context.meta_apis["analysis_api"]

    # GIVEN a case that is to be stored
    microsalt_case: Family = store.family(microsalt_case_qc_pass)
    microsalt_case.samples[1].control = "negative"
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
    microsalt_case: Family = store.family(microsalt_case_qc_fail)
    microsalt_case.samples[0].control = "negative"

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
