"""Test finish demultiplexing CLI."""
import logging
from pathlib import Path

from click import testing

from cg.cli.demultiplex.finish import finish_all_hiseq_x, finish_all_cmd, finish_flowcell
from cg.constants import EXIT_SUCCESS
from cg.models.cg_config import CGConfig


def test_finish_all_cmd_dry_run(
    caplog,
    cli_runner: testing.CliRunner,
    demultiplex_context: CGConfig,
    demultiplexed_flowcell_finished_working_directory: Path,
):
    caplog.set_level(logging.INFO)

    # GIVEN a demultiplex flow cell finished output directory that exist

    # GIVEN a demultiplex context

    # WHEN starting post-processing for new demultiplexing from the CLI with dry run flag
    result: testing.Result = cli_runner.invoke(
        finish_all_cmd,
        ["--dry-run"],
        obj=demultiplex_context,
    )

    # THEN assert the command exits successfully
    assert result.exit_code == EXIT_SUCCESS


def test_finish_all_cmd(
    caplog,
    cli_runner: testing.CliRunner,
    demultiplex_context: CGConfig,
    demultiplexed_flowcell_finished_working_directory: Path,
):
    caplog.set_level(logging.INFO)

    # GIVEN a demultiplex flow cell finished output directory that exist

    # GIVEN a demultiplex context

    # WHEN starting post-processing for new demultiplexing from the CLI
    result: testing.Result = cli_runner.invoke(
        finish_all_cmd,
        obj=demultiplex_context,
    )

    # THEN assert the command exits successfully
    assert result.exit_code == EXIT_SUCCESS


def test_finish_flowcell_dry_run(
    caplog,
    cli_runner: testing.CliRunner,
    demultiplex_context: CGConfig,
    demultiplexed_flowcell_finished_working_directory: Path,
    flow_cell_name: str,
):
    caplog.set_level(logging.INFO)

    # GIVEN a demultiplex flow cell finished output directory that exist

    # GIVEN a demultiplex context

    # GIVEN a flow cell

    # WHEN starting post-processing for new demultiplexing from the CLI with dry run flag
    result: testing.Result = cli_runner.invoke(
        finish_flowcell,
        ["--dry-run", flow_cell_name],
        obj=demultiplex_context,
    )

    # THEN assert the command exits successfully
    assert result.exit_code == EXIT_SUCCESS


def test_finish_flowcell(
    caplog,
    cli_runner: testing.CliRunner,
    demultiplex_context: CGConfig,
    demultiplexed_flowcell_finished_working_directory: Path,
    flow_cell_name: str,
):
    caplog.set_level(logging.INFO)

    # GIVEN a demultiplex flow cell finished output directory that exist

    # GIVEN a demultiplex context

    # GIVEN a flow cell

    # WHEN starting post-processing for new demultiplexing from the CLI
    result: testing.Result = cli_runner.invoke(
        finish_flowcell,
        [flow_cell_name],
        obj=demultiplex_context,
    )

    # THEN assert the command exits successfully
    assert result.exit_code == EXIT_SUCCESS


def test_finish_all_hiseq_x_dry_run(
    caplog,
    cli_runner: testing.CliRunner,
    demultiplex_context: CGConfig,
    demultiplexed_flowcell_finished_working_directory: Path,
):
    caplog.set_level(logging.INFO)

    # GIVEN a demultiplex flow cell finished output directory that exist

    # GIVEN a demultiplex context

    # WHEN starting post-processing for new demultiplexing from the CLI with dry run flag
    result: testing.Result = cli_runner.invoke(
        finish_all_hiseq_x,
        ["--dry-run"],
        obj=demultiplex_context,
    )

    # THEN assert the command exits successfully
    assert result.exit_code == EXIT_SUCCESS


def test_finish_all_hiseq_x(
    caplog,
    cli_runner: testing.CliRunner,
    demultiplex_context: CGConfig,
    demultiplexed_flowcell_finished_working_directory: Path,
):
    caplog.set_level(logging.INFO)

    # GIVEN a demultiplex flow cell finished output directory that exist

    # GIVEN a demultiplex context

    # WHEN starting post-processing for new demultiplexing from the CLI
    result: testing.Result = cli_runner.invoke(
        finish_all_hiseq_x,
        obj=demultiplex_context,
    )

    # THEN assert the command exits successfully
    assert result.exit_code == EXIT_SUCCESS
