"""Test the Gens upload command."""

import logging
from click.testing import CliRunner

from cg.constants import EXIT_SUCCESS
from cg.cli.upload.gens import upload_to_gens as upload_gens_cmd
from cg.models.cg_config import CGConfig


def test_upload_gens(
    caplog,
    case_id: str,
    cli_runner: CliRunner,
    upload_gens_context: CGConfig,
):
    """Test for Gens upload via the CLI."""
    caplog.set_level(logging.DEBUG)

    # WHEN uploading to Gens
    result = cli_runner.invoke(upload_gens_cmd, [case_id, "--dry-run"], obj=upload_gens_context)

    # THEN check that the command exits with success
    assert result.exit_code == EXIT_SUCCESS
    assert "Dry run" in caplog.text
