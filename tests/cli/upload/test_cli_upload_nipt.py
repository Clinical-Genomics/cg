"""Test module cg.cli.upload.nipt"""
import datetime
import logging

from cg.cli.upload.nipt.base import nipt_upload_case, nipt_upload_all
from cgmodels.cg.constants import Pipeline
from click.testing import CliRunner

from cg.models.cg_config import CGConfig


def test_nipt_statina_upload_case(upload_context: CGConfig, cli_runner: CliRunner, caplog, helpers):
    """Tests CLI command to upload a single case"""

    # GIVEN a specified NIPT case that has its analysis stored but is not yet uploaded
    caplog.set_level(logging.DEBUG)

    analysis_obj = helpers.add_analysis(store=upload_context.status_db)
    case_id = analysis_obj.family.internal_id
    assert not analysis_obj.upload_started_at
    assert not analysis_obj.uploaded_at

    # WHEN uploading of a specified NIPT case
    result = cli_runner.invoke(nipt_upload_case, [case_id], obj=upload_context)

    # THEN both the nipt ftp and statina upload should start
    assert "*** NIPT UPLOAD START ***" in caplog.text
    assert "*** Statina UPLOAD START ***" in caplog.text
    assert "*** NIPT FTP UPLOAD START ***" in caplog.text

    # THEN set analysis.upload_started_at in the database
    assert analysis_obj.upload_started_at

    # THEN set analysis.uploaded_at in the database
    assert analysis_obj.uploaded_at

    # THEN exit without errors
    assert result.exit_code == 0


def test_nipt_statina_upload_case_dry_run(
    upload_context: CGConfig, cli_runner: CliRunner, caplog, helpers
):
    """Tests CLI command to upload a single case"""

    # GIVEN a specified NIPT case that has its analysis stored but is not yet uploaded
    caplog.set_level(logging.DEBUG)

    analysis_obj = helpers.add_analysis(store=upload_context.status_db)
    case_id = analysis_obj.family.internal_id
    assert not analysis_obj.upload_started_at
    assert not analysis_obj.uploaded_at

    # WHEN uploading a specified NIPT case with dry-run flag set
    result = cli_runner.invoke(nipt_upload_case, [case_id, "--dry-run"], obj=upload_context)

    # THEN both the nipt ftp and statina upload should start
    assert "*** NIPT UPLOAD START ***" in caplog.text
    assert "*** Statina UPLOAD START ***" in caplog.text
    assert "*** NIPT FTP UPLOAD START ***" in caplog.text

    # THEN analysis.upload_started_at should not be set in the database
    assert analysis_obj.upload_started_at is None

    # THEN analysis.uploaded_at should not be set in the database
    assert analysis_obj.uploaded_at is None

    # THEN exit without errors
    assert result.exit_code == 0


def test_nipt_statina_upload_auto(upload_context: CGConfig, cli_runner: CliRunner, caplog, helpers):
    """Tests CLI command to upload a single case"""

    # GIVEN a case ready for upload
    caplog.set_level(logging.DEBUG)

    analysis_obj = helpers.add_analysis(
        store=upload_context.status_db,
        completed_at=datetime.datetime.now(),
        pipeline=Pipeline.FLUFFY,
    )
    assert analysis_obj.completed_at
    assert not analysis_obj.uploaded_at

    # WHEN uploading all NIPT cases
    result = cli_runner.invoke(nipt_upload_all, [], obj=upload_context)

    # THEN both the nipt ftp and statina upload should start
    assert "*** NIPT UPLOAD ALL START ***" in caplog.text
    assert "*** Statina UPLOAD START ***" in caplog.text
    assert "*** NIPT FTP UPLOAD START ***" in caplog.text

    # THEN set analysis.upload_started_at in the database
    assert analysis_obj.upload_started_at

    # THEN set analysis.uploaded_at in the database
    assert analysis_obj.uploaded_at

    # THEN exit without errors
    assert result.exit_code == 0


def test_nipt_statina_upload_auto_dry_run(
    upload_context: CGConfig, cli_runner: CliRunner, caplog, helpers
):
    """Tests CLI command to upload a single case"""

    # GIVEN a case ready for upload
    caplog.set_level(logging.DEBUG)

    analysis_obj = helpers.add_analysis(
        store=upload_context.status_db,
        completed_at=datetime.datetime.now(),
        pipeline=Pipeline.FLUFFY,
    )
    assert analysis_obj.completed_at
    assert not analysis_obj.uploaded_at

    # WHEN uploading all NIPT cases
    result = cli_runner.invoke(nipt_upload_all, ["--dry-run"], obj=upload_context)

    # THEN both the nipt ftp and statina upload should start
    assert "*** NIPT UPLOAD ALL START ***" in caplog.text
    assert "*** Statina UPLOAD START ***" in caplog.text
    assert "*** NIPT FTP UPLOAD START ***" in caplog.text

    # THEN analysis.upload_started_at should not be set in the database
    assert analysis_obj.upload_started_at is None

    # THEN analysis.uploaded_at should not be set in the database
    assert analysis_obj.uploaded_at is None

    # THEN exit without errors
    assert result.exit_code == 0
