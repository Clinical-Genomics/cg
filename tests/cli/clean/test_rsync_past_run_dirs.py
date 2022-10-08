import datetime as dt
import logging

from click.testing import CliRunner
from pathlib import Path

from cg.cli.workflow.commands import rsync_past_run_dirs
from cg.constants.process import EXIT_SUCCESS
from cg.models.cg_config import CGConfig


def test_clean_rsync_past_run_dirs_young_process(
    caplog,
    clean_context: CGConfig,
    cli_runner: CliRunner,
    rsync_process: Path,
    timestamp_now: dt.datetime,
):
    """
    Test that the clean function does not remove newly created dirs.
    rsync_process is always created at the time of the test
    """

    caplog.set_level(logging.INFO)
    # GIVEN a newly created rsync_process
    assert rsync_process.exists()
    # WHEN attempting to remove said process same day
    result = cli_runner.invoke(
        rsync_past_run_dirs, ["-d", "-y", str(timestamp_now)], obj=clean_context
    )
    # THEN the command should not fail and notice that the process is not old
    assert result.exit_code == EXIT_SUCCESS
    assert f"{rsync_process.as_posix()} is still young" in caplog.text


def test_clean_rsync_past_run_dirs_old_process(
    caplog,
    clean_context: CGConfig,
    cli_runner: CliRunner,
    rsync_process: Path,
    timestamp_in_2_weeks: dt.datetime,
):
    """Test that the clean function does remove old dirs. rsync_process is always created at the time of the test"""

    caplog.set_level(logging.INFO)
    # GIVEN a newly created rsync process
    assert rsync_process.exists()
    # WHEN trying to remove it 2 weeks in the future
    result = cli_runner.invoke(
        rsync_past_run_dirs, ["-y", str(timestamp_in_2_weeks)], obj=clean_context
    )
    # THEN it should not fail, inform what process that is removed and it should not exist any more
    assert result.exit_code == EXIT_SUCCESS
    assert f"Removing {rsync_process.as_posix()}" in caplog.text
    assert not rsync_process.exists()
