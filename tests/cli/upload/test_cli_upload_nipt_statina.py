"""Test module cg.cli.upload.nipt"""

import logging

from click.testing import CliRunner

from cg.cli.upload.nipt.statina import batch
from cg.models.cg_config import CGConfig


def test_nipt_statina_upload_case(upload_context: CGConfig, cli_runner: CliRunner, caplog):
    """Tests CLI command to upload a single case"""

    caplog.set_level(logging.DEBUG)
    # GIVEN a specified NIPT case
    case_id = "angrybird"

    # WHEN adding a result file of a specified NIPT case
    # result = cli_runner.invoke(nipt_upload_case, ["--dry-run", case_id], obj=upload_context)
    result = cli_runner.invoke(batch, [case_id], obj=upload_context)

    # THEN the nipt upload should start and exit without errors
    assert "*** Statina UPLOAD START ***" in caplog.text
    assert result.exit_code == 0


def test_nipt_statina_upload_case_dry(upload_context: CGConfig, cli_runner: CliRunner, caplog):
    """Tests CLI command to upload a single case"""

    caplog.set_level(logging.DEBUG)
    # GIVEN a specified NIPT case
    case_id = "angrybird"

    # WHEN adding a result file of a specified NIPT case (dry run)
    result = cli_runner.invoke(batch, ["--dry-run", case_id], obj=upload_context)

    # THEN the nipt upload should start and exit without errors
    assert "*** Statina UPLOAD START ***" in caplog.text
    assert result.exit_code == 0
