"""Test module cg.cli.upload.gisaid"""

import logging

from click.testing import CliRunner

from cg.cli.upload.gisaid import gisaid
from cg.models.cg_config import CGConfig


def test_nipt_upload_case(upload_context: CGConfig, cli_runner: CliRunner, caplog):
    """Tests CLI command to upload a single case"""

    caplog.set_level(logging.DEBUG)
    # GIVEN a specified NIPT case
    case_id = "angrybird"

    # WHEN running the upload gisaid command with a case
    result = cli_runner.invoke(gisaid, [case_id], obj=upload_context)

    # THEN the nipt upload should start and exit without errors
    assert "*** NIPT UPLOAD START ***" in caplog.text
    assert result.exit_code == 0


def test_nipt_upload_case_dry(upload_context: CGConfig, cli_runner: CliRunner, caplog):
    """Tests CLI command to upload a single case"""

    caplog.set_level(logging.DEBUG)
    # GIVEN a specified NIPT case
    case_id = "angrybird"

    # WHEN adding a result file of a specified NIPT case (dry run)
    result = cli_runner.invoke(gisaid, ["--dry-run", case_id], obj=upload_context)

    # THEN the nipt upload should start and exit without errors
    assert "*** NIPT UPLOAD START ***" in caplog.text
    assert result.exit_code == 0
