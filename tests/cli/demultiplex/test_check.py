"""Test check demultiplexing CLI."""
import logging
from pathlib import Path

from click import testing

from cg.cli.demultiplex.check import check_new_demultiplex
from cg.constants import EXIT_SUCCESS
from cg.models.cg_config import CGConfig


def test_check_new_demultiplex_dry_run(
    cli_runner: testing.CliRunner,
    demultiplex_context: CGConfig,
    demultiplexed_flowcell_finished_working_directory: Path,
    caplog,
):
    caplog.set_level(logging.INFO)

    # GIVEN a demultiplex flow cell finished output directory that exist

    # GIVEN a demultiplex context

    # WHEN starting check for new demultiplexing from the CLI with dry run flag
    result: testing.Result = cli_runner.invoke(
        check_new_demultiplex,
        ["--dry-run"],
        obj=demultiplex_context,
    )
    print(caplog.records)

    # THEN assert the command exits without problems
    assert result.exit_code == EXIT_SUCCESS
