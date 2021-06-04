"""Test module cg.cli.upload.nipt"""

import logging

from click.testing import CliRunner

from cg.cli.upload.nipt.ftp import nipt_upload_all, nipt_upload_case
from cg.models.cg_config import CGConfig


def test_nipt_upload_case(upload_context: CGConfig, cli_runner: CliRunner, caplog):
    """Tests CLI command to upload a single case"""

    caplog.set_level(logging.DEBUG)
    # GIVEN a specified NIPT case
    case_id = "angrybird"

    # WHEN adding a result file of a specified NIPT case
    # result = cli_runner.invoke(nipt_upload_case, ["--dry-run", case_id], obj=upload_context)
    result = cli_runner.invoke(nipt_upload_case, [case_id], obj=upload_context)

    # THEN the nipt upload should start and exit without errors
    assert "*** NIPT FTP UPLOAD START ***" in caplog.text
    assert result.exit_code == 0


def test_nipt_upload_case_dry(upload_context: CGConfig, cli_runner: CliRunner, caplog):
    """Tests CLI command to upload a single case"""

    caplog.set_level(logging.DEBUG)
    # GIVEN a specified NIPT case
    case_id = "angrybird"

    # WHEN adding a result file of a specified NIPT case (dry run)
    result = cli_runner.invoke(nipt_upload_case, ["--dry-run", case_id], obj=upload_context)

    # THEN the nipt upload should start and exit without errors
    assert "*** NIPT FTP UPLOAD START ***" in caplog.text
    assert result.exit_code == 0


def test_nipt_upload_all(upload_context: CGConfig, cli_runner: CliRunner, caplog):
    """Tests CLI command to upload a single case"""

    caplog.set_level(logging.DEBUG)
    # GIVEN adding all available NIPT case results

    # WHEN adding a result file of a all available NIPT cases
    result = cli_runner.invoke(nipt_upload_all, obj=upload_context)

    # THEN the NIPT upload should start and exit without errors
    assert "*** UPLOAD ALL AVAILABLE NIPT RESULTS ***" in caplog.text
    assert result.exit_code == 0


def test_nipt_upload_all_dry(upload_context: CGConfig, cli_runner: CliRunner, caplog):
    """Tests CLI command to upload a single case"""

    caplog.set_level(logging.DEBUG)
    # GIVEN adding all available NIPT case results

    # WHEN adding a result file of a all available NIPT cases (dry run)
    result = cli_runner.invoke(nipt_upload_all, ["--dry-run"], obj=upload_context)

    # THEN the NIPT upload should start and exit without errors
    assert "*** UPLOAD ALL AVAILABLE NIPT RESULTS ***" in caplog.text
    assert result.exit_code == 0
