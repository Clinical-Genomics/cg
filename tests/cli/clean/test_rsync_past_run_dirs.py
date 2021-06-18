import datetime as dt
import logging

from click.testing import CliRunner
from pathlib import Path

from cg.cli.workflow.commands import rsync_past_run_dirs
from cg.constants.process import EXIT_SUCCESS
from cg.models.cg_config import CGConfig


def test_clean_rsync_past_run_dirs_young_process(
    clean_context: CGConfig,
    cli_runner: CliRunner,
    rsync_process: Path,
    timestamp_today: dt.datetime,
    caplog,
):
    """
    Test that the clean function does not remove newly created dirs.
    rsync_process is always created at the time of the test
    """

    caplog.set_level(logging.INFO)
    assert rsync_process.exists()
    result = cli_runner.invoke(
        rsync_past_run_dirs, ["-d", "-y", str(timestamp_today)], obj=clean_context
    )
    assert result.exit_code == EXIT_SUCCESS
    assert f"{rsync_process.as_posix()} is still young" in caplog.text


def test_clean_rsync_past_run_dirs_old_process(
    clean_context: CGConfig,
    cli_runner: CliRunner,
    rsync_process: Path,
    timestamp_in_2_weeks: dt.datetime,
    caplog,
):
    """Test that the clean function does remove old dirs. rsync_process is always created at the time of the test"""

    caplog.set_level(logging.INFO)
    assert rsync_process.exists()
    result = cli_runner.invoke(
        rsync_past_run_dirs, ["-d", "-y", str(timestamp_in_2_weeks)], obj=clean_context
    )
    assert result.exit_code == EXIT_SUCCESS
    assert f"Would have removed {rsync_process}" in caplog.text
