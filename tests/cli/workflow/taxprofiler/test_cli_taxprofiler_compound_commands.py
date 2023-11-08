import logging

from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner

from cg.cli.workflow.taxprofiler.base import start, start_available, taxprofiler
from cg.constants import EXIT_SUCCESS
from cg.exc import CgError
from cg.meta.workflow.taxprofiler import TaxprofilerAnalysisAPI
from cg.models.cg_config import CGConfig


def test_taxprofiler_no_args(cli_runner: CliRunner, taxprofiler_context: CGConfig):
    """Test to see that running Taxprofiler without options prints help and doesn't result in an error."""
    # GIVEN no arguments or options besides the command call

    # WHEN running command
    result = cli_runner.invoke(taxprofiler, [], obj=taxprofiler_context)

    assert result.exit_code == EXIT_SUCCESS

    ## THEN help should be printed
    assert "help" in result.output


def test_taxprofiler_start(
    cli_runner: CliRunner,
    taxprofiler_context: CGConfig,
    caplog: LogCaptureFixture,
    taxprofiler_case_id: str,
):
    """Test to ensure all parts of start command will run successfully given ideal conditions."""
    caplog.set_level(logging.INFO)

    # GIVEN case id
    case_id: str = taxprofiler_case_id

    # GIVEN a mocked config

    TaxprofilerAnalysisAPI.resolve_decompression.return_value = None

    # WHEN dry running with dry specified
    result = cli_runner.invoke(start, [case_id, "--dry-run"], obj=taxprofiler_context)

    # THEN command should execute successfully
    assert result.exit_code == EXIT_SUCCESS
    assert case_id in caplog.text

    # THEN command should not include resume flag
    assert "-resume" not in caplog.text


def test_taxprofiler_start_available(
    cli_runner: CliRunner,
    taxprofiler_context: CGConfig,
    caplog: LogCaptureFixture,
    taxprofiler_case_id: str,
):
    """Test that start-available picks up the available cases that are ready for analysis."""
    caplog.set_level(logging.INFO)

    # GIVEN case id with enough reads

    # GIVEN a mocked config

    # GIVEN decompression is not needed
    TaxprofilerAnalysisAPI.resolve_decompression.return_value = None

    # WHEN running command
    result = cli_runner.invoke(start_available, ["--dry-run"], obj=taxprofiler_context)

    # THEN command exits with 0
    assert result.exit_code == EXIT_SUCCESS

    # THEN it should successfully identify the one case eligible for auto-start
    assert taxprofiler_case_id in caplog.text
