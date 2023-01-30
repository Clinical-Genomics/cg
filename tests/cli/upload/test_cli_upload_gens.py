"""Test the Gens upload command"""

import logging

from cg.constants import EXIT_SUCCESS
from cg.cli.upload.gens import gens as upload_gens_cmd
from cg.models.cg_config import CGConfig
from click.testing import CliRunner


def test_upload_gens(
    upload_context: CGConfig,
    case_id: str,
    cli_runner: CliRunner,
    caplog,
):
    """Test for Gens upload via the CLI"""
    caplog.set_level(logging.DEBUG)

    # WHEN uploading to Gens
    result = cli_runner.invoke(upload_gens_cmd, [case_id, "--dry-run"], obj=upload_context)

    # THEN check that the command exits with success
    assert result.exit_code == EXIT_SUCCESS

    # THEN assert the correct information is communicated
    assert f"Dry run. Would upload data for {case_id} to Gens." in caplog.text
