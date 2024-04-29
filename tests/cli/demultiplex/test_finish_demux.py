"""Test finish demultiplexing CLI."""

import logging

from click import testing

from cg.cli.demultiplex.finish import finish_all_cmd, finish_flow_cell
from cg.constants import EXIT_SUCCESS
from cg.models.cg_config import CGConfig


def test_finish_all_cmd_dry_run(
    caplog,
    cli_runner: testing.CliRunner,
    demultiplex_context: CGConfig,
    tmp_illumina_demultiplexed_flow_cells_directory,
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


def test_finish_flow_cell_dry_run(
    caplog,
    cli_runner: testing.CliRunner,
    demultiplex_context: CGConfig,
    tmp_illumina_demultiplexed_flow_cells_directory,
    novaseq_6000_pre_1_5_kits_flow_cell_full_name: str,
):
    caplog.set_level(logging.INFO)

    # GIVEN a demultiplex flow cell finished output directory that exist

    # GIVEN a demultiplex context

    # GIVEN a flow cell id

    # WHEN starting post-processing for new demultiplexing from the CLI with dry run flag
    result: testing.Result = cli_runner.invoke(
        finish_flow_cell,
        ["--dry-run", novaseq_6000_pre_1_5_kits_flow_cell_full_name],
        obj=demultiplex_context,
    )

    # THEN assert the command exits successfully
    assert result.exit_code == EXIT_SUCCESS
