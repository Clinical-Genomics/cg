"""Test module cg.cli.upload.nipt"""

import logging

from click.testing import CliRunner

from cg.cli.upload.nipt import nipt
from cg.models.cg_config import CGConfig


def test_nipt_statina_upload_case(upload_context: CGConfig, cli_runner: CliRunner, caplog, helpers):
    """Tests CLI command to upload a single case"""

    # GIVEN a specified NIPT case that has its analysis stored but is not yet uploaded
    caplog.set_level(logging.DEBUG)

    analysis_obj = helpers.add_analysis(store=upload_context.status_db)
    case_id = analysis_obj.family.internal_id
    assert not analysis_obj.upload_started_at
    assert not analysis_obj.uploaded_at

    # WHEN adding a result file of a specified NIPT case
    result = cli_runner.invoke(nipt, ['-c', case_id], obj=upload_context, catch_exceptions=False)

    # THEN both the nipt ftp and statina upload should start
    assert "*** Statina UPLOAD START ***" in caplog.text
    assert "*** NIPT FTP UPLOAD START ***" in caplog.text

    # THEN set analysis.upload_started_at in the database
    assert analysis_obj.upload_started_at

    # THEN set analysis.uploaded_at in the database
    assert analysis_obj.uploaded_at

    # THEN exit without errors
    assert result.exit_code == 0
