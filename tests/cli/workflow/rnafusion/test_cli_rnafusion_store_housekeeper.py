import logging

from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner

from cg.cli.workflow.rnafusion.base import store_housekeeper
from cg.constants import EXIT_SUCCESS
from cg.models.cg_config import CGConfig


def test_case_not_finished(
    cli_runner: CliRunner,
    rnafusion_context: CGConfig,
    caplog: LogCaptureFixture,
    rnafusion_case_id: str,
):
    """Test command with case_id and config file but no analysis_finish."""
    caplog.set_level(logging.ERROR)
    # GIVEN case-id
    case_id: str = rnafusion_case_id

    # WHEN running
    result = cli_runner.invoke(store_housekeeper, [case_id], obj=rnafusion_context)

    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS

    # THEN warning should be printed that no deliverables file has been found
    assert "No deliverables file found for case" in caplog.text
