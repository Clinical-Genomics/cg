"""Test module cg.cli.upload.nipt"""
import datetime
import logging

from click.testing import CliRunner

from cg.cli.upload.nipt.base import nipt_upload_all, nipt_upload_case
from cg.meta.upload.nipt import NiptUploadAPI
from cg.apps.tb.api import TrailblazerAPI
from cg.models.cg_config import CGConfig
from cgmodels.cg.constants import Pipeline
from cg.store.models import Analysis

NIPT_CASE_SUCCESS = "*** NIPT UPLOAD START ***"
NIPT_ALL_SUCCESS = "*** NIPT UPLOAD ALL START ***"
NIPT_STATINA_SUCCESS = "*** Statina UPLOAD START ***"
NIPT_FTP_SUCCESS = "*** NIPT FTP UPLOAD START ***"


class MockStatinaUploadFiles:
    def json(self, *args, **kwargs):
        return ""


def test_nipt_statina_upload_case(
    upload_context: CGConfig, cli_runner: CliRunner, caplog, helpers, mocker
):
    """Tests CLI command to upload a single case"""

    # GIVEN a specified NIPT case that has its analysis stored but is not yet uploaded
    caplog.set_level(logging.DEBUG)

    analysis_obj: Analysis = helpers.add_analysis(store=upload_context.status_db)
    case_id = analysis_obj.family.internal_id
    assert not analysis_obj.upload_started_at
    assert not analysis_obj.uploaded_at

    # WHEN uploading of a specified NIPT case
    mocker.patch.object(NiptUploadAPI, "get_statina_files", return_value=MockStatinaUploadFiles())
    mocker.patch.object(NiptUploadAPI, "upload_to_statina_database")
    mocker.patch.object(NiptUploadAPI, "get_housekeeper_results_file")
    mocker.patch.object(NiptUploadAPI, "get_results_file_path")
    mocker.patch.object(NiptUploadAPI, "upload_to_ftp_server")
    mocker.patch.object(NiptUploadAPI, "flowcell_passed_qc_value", return_value=True)
    mocker.patch.object(TrailblazerAPI, "set_analysis_uploaded")
    result = cli_runner.invoke(
        cli=nipt_upload_case, args=[case_id], obj=upload_context, catch_exceptions=False
    )

    # THEN both the nipt ftp and statina upload should start
    assert NIPT_CASE_SUCCESS in caplog.text
    assert NIPT_STATINA_SUCCESS in caplog.text
    assert NIPT_FTP_SUCCESS in caplog.text

    # THEN set analysis.upload_started_at in the database
    assert analysis_obj.upload_started_at

    # THEN set analysis.uploaded_at in the database
    assert analysis_obj.uploaded_at

    # THEN exit without errors
    assert result.exit_code == 0


def test_nipt_statina_upload_case_dry_run(
    upload_context: CGConfig, cli_runner: CliRunner, caplog, helpers, mocker
):
    """Tests CLI command to upload a single case"""

    # GIVEN a specified NIPT case that has its analysis stored but is not yet uploaded
    caplog.set_level(logging.DEBUG)

    analysis_obj: Analysis = helpers.add_analysis(store=upload_context.status_db)
    case_id = analysis_obj.family.internal_id
    assert not analysis_obj.upload_started_at
    assert not analysis_obj.uploaded_at

    # WHEN uploading a specified NIPT case with dry-run flag set
    mocker.patch.object(NiptUploadAPI, "get_statina_files", return_value=MockStatinaUploadFiles())
    mocker.patch.object(NiptUploadAPI, "upload_to_statina_database")
    mocker.patch.object(NiptUploadAPI, "get_housekeeper_results_file")
    mocker.patch.object(NiptUploadAPI, "get_results_file_path")
    mocker.patch.object(NiptUploadAPI, "upload_to_ftp_server")
    mocker.patch.object(NiptUploadAPI, "flowcell_passed_qc_value", return_value=True)
    result = cli_runner.invoke(
        cli=nipt_upload_case, args=[case_id, "--dry-run"], obj=upload_context
    )

    # THEN both the nipt ftp and statina upload should start
    assert NIPT_CASE_SUCCESS in caplog.text
    assert NIPT_STATINA_SUCCESS in caplog.text
    assert NIPT_FTP_SUCCESS in caplog.text

    # THEN analysis.upload_started_at should not be set in the database
    assert analysis_obj.upload_started_at is None

    # THEN analysis.uploaded_at should not be set in the database
    assert analysis_obj.uploaded_at is None

    # THEN exit without errors
    assert result.exit_code == 0


def test_nipt_statina_upload_auto(
    upload_context: CGConfig, cli_runner: CliRunner, caplog, helpers, mocker
):
    """Tests CLI command to upload a single case"""

    # GIVEN a case ready for upload
    caplog.set_level(logging.DEBUG)

    analysis_obj: Analysis = helpers.add_analysis(
        store=upload_context.status_db,
        completed_at=datetime.datetime.now(),
        pipeline=Pipeline.FLUFFY,
    )
    assert analysis_obj.completed_at
    assert not analysis_obj.uploaded_at

    # WHEN uploading all NIPT cases
    mocker.patch.object(NiptUploadAPI, "get_statina_files", return_value=MockStatinaUploadFiles())
    mocker.patch.object(NiptUploadAPI, "upload_to_statina_database")
    mocker.patch.object(NiptUploadAPI, "get_housekeeper_results_file")
    mocker.patch.object(NiptUploadAPI, "get_results_file_path")
    mocker.patch.object(NiptUploadAPI, "upload_to_ftp_server")
    mocker.patch.object(NiptUploadAPI, "flowcell_passed_qc_value", return_value=True)
    mocker.patch.object(TrailblazerAPI, "set_analysis_uploaded")

    result = cli_runner.invoke(cli=nipt_upload_all, args=[], obj=upload_context)

    # THEN both the nipt ftp and statina upload should start
    assert NIPT_ALL_SUCCESS in caplog.text
    assert NIPT_STATINA_SUCCESS in caplog.text
    assert NIPT_FTP_SUCCESS in caplog.text

    # THEN set analysis.upload_started_at in the database
    assert analysis_obj.upload_started_at

    # THEN set analysis.uploaded_at in the database
    assert analysis_obj.uploaded_at

    # THEN exit without errors
    assert result.exit_code == 0


def test_nipt_statina_upload_auto_without_analyses(
    upload_context: CGConfig, cli_runner: CliRunner, caplog, helpers, mocker
):
    """Tests CLI command to upload without any analyses to upload."""

    # GIVEN no analyses for upload
    caplog.set_level(logging.DEBUG)

    mocker.patch.object(NiptUploadAPI, "get_all_upload_analyses", return_value=None)

    # WHEN uploading all NIPT cases
    result = cli_runner.invoke(cli=nipt_upload_all, args=[], obj=upload_context)

    # THEN the command should abort without raising an error
    assert result.exit_code == 0
    assert "No analyses found to upload" in caplog.text


def test_nipt_statina_upload_auto_analysis_without_case(
    upload_context: CGConfig, cli_runner: CliRunner, caplog, helpers, mocker
):
    """Tests CLI command to upload a non-existing case."""

    # GIVEN no analyses for upload
    caplog.set_level(logging.DEBUG)

    analysis_obj: Analysis = helpers.add_analysis(
        store=upload_context.status_db,
        completed_at=datetime.datetime.now(),
        pipeline=Pipeline.FLUFFY,
    )
    analysis_obj.family = None
    mocker.patch.object(NiptUploadAPI, "get_all_upload_analyses", return_value=[analysis_obj])
    # WHEN uploading all NIPT cases
    result = cli_runner.invoke(cli=nipt_upload_all, args=[], obj=upload_context)

    # THEN the command should abort without raising an error
    assert result.exit_code != 0


def test_nipt_statina_upload_auto_dry_run(
    upload_context: CGConfig, cli_runner: CliRunner, caplog, helpers, mocker
):
    """Tests CLI command to upload a single case"""

    # GIVEN a case ready for upload
    caplog.set_level(logging.DEBUG)

    analysis_obj: Analysis = helpers.add_analysis(
        store=upload_context.status_db,
        completed_at=datetime.datetime.now(),
        pipeline=Pipeline.FLUFFY,
    )
    assert analysis_obj.completed_at
    assert not analysis_obj.uploaded_at

    # WHEN uploading all NIPT cases
    mocker.patch.object(NiptUploadAPI, "get_statina_files", return_value=MockStatinaUploadFiles())
    mocker.patch.object(NiptUploadAPI, "upload_to_statina_database")
    mocker.patch.object(NiptUploadAPI, "get_housekeeper_results_file")
    mocker.patch.object(NiptUploadAPI, "get_results_file_path")
    mocker.patch.object(NiptUploadAPI, "upload_to_ftp_server")
    mocker.patch.object(NiptUploadAPI, "flowcell_passed_qc_value", return_value=True)
    result = cli_runner.invoke(cli=nipt_upload_all, args=["--dry-run"], obj=upload_context)

    # THEN both the nipt ftp and statina upload should start
    assert NIPT_ALL_SUCCESS in caplog.text
    assert NIPT_STATINA_SUCCESS in caplog.text
    assert NIPT_FTP_SUCCESS in caplog.text

    # THEN analysis.upload_started_at should not be set in the database
    assert analysis_obj.upload_started_at is None

    # THEN analysis.uploaded_at should not be set in the database
    assert analysis_obj.uploaded_at is None

    # THEN exit without errors
    assert result.exit_code == 0


def test_nipt_statina_upload_force_failed_case(
    upload_context: CGConfig, cli_runner: CliRunner, caplog, helpers, mocker
):
    """Tests CLI command to upload a single case"""

    # GIVEN a completed NIPT case, not yet uploaded
    caplog.set_level(logging.DEBUG)

    analysis_obj: Analysis = helpers.add_analysis(store=upload_context.status_db)
    case_id = analysis_obj.family.internal_id

    # WHEN uploading of a specified NIPT case AND the qc fails but it forced to upload
    mocker.patch.object(NiptUploadAPI, "get_statina_files", return_value=MockStatinaUploadFiles())
    mocker.patch.object(NiptUploadAPI, "upload_to_statina_database")
    mocker.patch.object(NiptUploadAPI, "get_housekeeper_results_file")
    mocker.patch.object(NiptUploadAPI, "get_results_file_path")
    mocker.patch.object(NiptUploadAPI, "upload_to_ftp_server")
    mocker.patch.object(NiptUploadAPI, "flowcell_passed_qc_value", return_value=False)
    mocker.patch.object(TrailblazerAPI, "set_analysis_uploaded")
    result = cli_runner.invoke(
        cli=nipt_upload_case, args=[case_id, "--force"], obj=upload_context, catch_exceptions=False
    )

    # THEN both the nipt ftp and statina upload should finish successfully
    assert NIPT_CASE_SUCCESS in caplog.text
    assert NIPT_STATINA_SUCCESS in caplog.text
    assert NIPT_FTP_SUCCESS in caplog.text

    # THEN exit without errors
    assert result.exit_code == 0
