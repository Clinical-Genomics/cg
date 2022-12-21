"""This script tests the start cli command"""
import logging
from pathlib import Path

from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner

from cg.cli.workflow.rnafusion.base import start
from cg.constants import EXIT_SUCCESS
from cg.models.cg_config import CGConfig


def test_start_with_config(
    cli_runner: CliRunner,
    rnafusion_context: CGConfig,
    caplog: LogCaptureFixture,
    rnafusion_case_id: str,
):
    """Test command with case_id and config file."""
    caplog.set_level(logging.INFO)
    # GIVEN case-id
    case_id: str = rnafusion_case_id
    # WHEN ensuring case config exists where it should be stored
    Path.mkdir(
        Path(rnafusion_context.meta_apis["analysis_api"].get_case_config_path(case_id)).parent,
        exist_ok=True,
    )
    Path(rnafusion_context.meta_apis["analysis_api"].get_case_config_path(case_id)).touch(
        exist_ok=True
    )
    # WHEN dry running with dry specified
    result = cli_runner.invoke(start, [case_id, "--dry-run"], obj=rnafusion_context)

    # THEN command should execute successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN command should not include resume flag
    assert "-resume" not in caplog.text
