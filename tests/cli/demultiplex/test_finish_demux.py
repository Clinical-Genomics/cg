"""Test finish demultiplexing CLI."""
import logging
from pathlib import Path

from click import testing

from cg.cli.demultiplex.finish import finish_all_hiseq_x, finish_all_cmd, finish_flow_cell
from cg.constants import EXIT_SUCCESS
from cg.models.cg_config import CGConfig


def test_finish_all_cmd_dry_run(
    caplog,
    cli_runner: testing.CliRunner,
    demultiplex_context: CGConfig,
    demultiplexed_flow_cell_finished_working_directory: Path,
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
    demultiplexed_flow_cell_finished_working_directory: Path,
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


def test_finish_flow_cell_dry_run(
    caplog,
    cli_runner: testing.CliRunner,
    demultiplex_context: CGConfig,
    demultiplexed_flow_cell_finished_working_directory: Path,
    flow_cell_id: str,
):
    caplog.set_level(logging.INFO)

    # GIVEN a demultiplex flow cell finished output directory that exist

    # GIVEN a demultiplex context

    # GIVEN a flow cell id

    # WHEN starting post-processing for new demultiplexing from the CLI with dry run flag
    result: testing.Result = cli_runner.invoke(
        finish_flow_cell,
        ["--dry-run", flow_cell_id],
        obj=demultiplex_context,
    )

    # THEN assert the command exits successfully
    assert result.exit_code == EXIT_SUCCESS


def test_finish_flow_cell(
    caplog,
    cli_runner: testing.CliRunner,
    demultiplex_context: CGConfig,
    demultiplexed_flow_cell_finished_working_directory: Path,
    flow_cell_id: str,
):
    caplog.set_level(logging.INFO)

    # GIVEN a demultiplex flow cell finished output directory that exist

    # GIVEN a demultiplex context

    # GIVEN a flow cell id

    # WHEN starting post-processing for new demultiplexing from the CLI
    result: testing.Result = cli_runner.invoke(
        finish_flow_cell,
        [flow_cell_id],
        obj=demultiplex_context,
    )

    # THEN assert the command exits successfully
    assert result.exit_code == EXIT_SUCCESS


def test_finish_all_hiseq_x_dry_run(
    caplog,
    cli_runner: testing.CliRunner,
    demultiplex_context: CGConfig,
    demultiplexed_flow_cell_finished_working_directory: Path,
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
    demultiplexed_flow_cell_finished_working_directory: Path,
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
