"""Test module cg.cli.upload.nipt.ftp"""

import logging

from click.testing import CliRunner

from cg.cli.upload.nipt.ftp import nipt_upload_all, nipt_upload_case
from cg.meta.upload.nipt import NiptUploadAPI
from cg.models.cg_config import CGConfig


def test_nipt_upload_case(upload_context: CGConfig, cli_runner: CliRunner, caplog, mocker):
    """Tests CLI command to upload a single case"""

    caplog.set_level(logging.DEBUG)
    # GIVEN a specified NIPT case
    case_id = "angrybird"

    # WHEN adding a result file of a specified NIPT case
    mocker.patch.object(NiptUploadAPI, "get_housekeeper_results_file")
    mocker.patch.object(NiptUploadAPI, "get_results_file_path")
    mocker.patch.object(NiptUploadAPI, "upload_to_ftp_server")
    mocker.patch.object(NiptUploadAPI, "flowcell_passed_qc_value")
    result = cli_runner.invoke(nipt_upload_case, [case_id], obj=upload_context)

    # THEN the nipt upload should start and exit without errors
    assert "*** NIPT FTP UPLOAD START ***" in caplog.text
    assert result.exit_code == 0


def test_nipt_upload_case_dry(upload_context: CGConfig, cli_runner: CliRunner, caplog, mocker):
    """Tests CLI command to upload a single case"""

    caplog.set_level(logging.DEBUG)
    # GIVEN a specified NIPT case
    case_id = "angrybird"

    # WHEN adding a result file of a specified NIPT case (dry run)
    mocker.patch.object(NiptUploadAPI, "get_housekeeper_results_file")
    mocker.patch.object(NiptUploadAPI, "get_results_file_path")
    mocker.patch.object(NiptUploadAPI, "upload_to_ftp_server")
    mocker.patch.object(NiptUploadAPI, "flowcell_passed_qc_value")
    result = cli_runner.invoke(nipt_upload_case, ["--dry-run", case_id], obj=upload_context)

    # THEN the nipt upload should start and exit without errors
    assert "*** NIPT FTP UPLOAD START ***" in caplog.text
    assert result.exit_code == 0


def test_nipt_upload_all(upload_context: CGConfig, cli_runner: CliRunner, caplog, mocker):
    """Tests CLI command to upload a single case"""

    caplog.set_level(logging.DEBUG)
    # GIVEN adding all available NIPT case results

    # WHEN adding a result file of a all available NIPT cases
    mocker.patch.object(NiptUploadAPI, "get_housekeeper_results_file")
    mocker.patch.object(NiptUploadAPI, "get_results_file_path")
    mocker.patch.object(NiptUploadAPI, "upload_to_ftp_server")
    mocker.patch.object(NiptUploadAPI, "flowcell_passed_qc_value")
    result = cli_runner.invoke(nipt_upload_all, obj=upload_context)

    # THEN the NIPT upload should start and exit without errors
    assert "*** UPLOAD ALL AVAILABLE NIPT RESULTS ***" in caplog.text
    assert result.exit_code == 0


def test_nipt_upload_all_dry(upload_context: CGConfig, cli_runner: CliRunner, caplog, mocker):
    """Tests CLI command to upload a single case"""

    caplog.set_level(logging.DEBUG)
    # GIVEN adding all available NIPT case results

    # WHEN adding a result file of a all available NIPT cases (dry run)
    mocker.patch.object(NiptUploadAPI, "get_housekeeper_results_file")
    mocker.patch.object(NiptUploadAPI, "get_results_file_path")
    mocker.patch.object(NiptUploadAPI, "upload_to_ftp_server")
    mocker.patch.object(NiptUploadAPI, "flowcell_passed_qc_value")
    result = cli_runner.invoke(nipt_upload_all, ["--dry-run"], obj=upload_context)

    # THEN the NIPT upload should start and exit without errors
    assert "*** UPLOAD ALL AVAILABLE NIPT RESULTS ***" in caplog.text
    assert result.exit_code == 0


def test_nipt_upload_case_not_changing_uploaded_at(
    upload_context: CGConfig, cli_runner: CliRunner, caplog, helpers, mocker
):
    """Tests CLI command to upload a single case"""

    # GIVEN a specified NIPT case that has its analysis stored but is not yet uploaded
    caplog.set_level(logging.DEBUG)

    analysis_obj = helpers.add_analysis(store=upload_context.status_db)
    case_id = analysis_obj.family.internal_id
    assert not analysis_obj.upload_started_at
    assert not analysis_obj.uploaded_at

    # WHEN adding a result file of a specified NIPT case
    mocker.patch.object(NiptUploadAPI, "get_housekeeper_results_file")
    mocker.patch.object(NiptUploadAPI, "get_results_file_path")
    mocker.patch.object(NiptUploadAPI, "upload_to_ftp_server")
    mocker.patch.object(NiptUploadAPI, "flowcell_passed_qc_value")
    result = cli_runner.invoke(nipt_upload_case, [case_id], obj=upload_context)

    # THEN set analysis.upload_started_at in the database
    assert not analysis_obj.upload_started_at

    # THEN set analysis.uploaded_at in the database
    assert not analysis_obj.uploaded_at

    # THEN exit without errors
    assert result.exit_code == 0
