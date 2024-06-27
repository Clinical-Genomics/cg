"""Test finish demultiplexing CLI."""

import logging

from click import testing

from cg.cli.demultiplex.finish import post_process_all_illumina_runs, post_process_illumina_run
from cg.constants import EXIT_SUCCESS
from cg.models.cg_config import CGConfig


def test_post_process_all_cmd_dry_run(
    caplog,
    cli_runner: testing.CliRunner,
    demultiplex_context: CGConfig,
    novaseq_x_flow_cell_id,
    hiseq_2500_custom_index_flow_cell_id,
    hiseq_x_single_index_flow_cell_id,
    hiseq_x_dual_index_flow_cell_id,
    novaseq_6000_pre_1_5_kits_flow_cell_id,
    novaseq_6000_post_1_5_kits_flow_cell_id,
    hiseq_2500_dual_index_flow_cell_id,
):
    caplog.set_level(logging.INFO)

    # GIVEN a demultiplex flow cell finished output directory that exist

    # GIVEN a demultiplex context
    fc_list = [
        novaseq_x_flow_cell_id,
        hiseq_2500_custom_index_flow_cell_id,
        hiseq_x_single_index_flow_cell_id,
        hiseq_x_dual_index_flow_cell_id,
        novaseq_6000_pre_1_5_kits_flow_cell_id,
        novaseq_6000_post_1_5_kits_flow_cell_id,
        hiseq_2500_dual_index_flow_cell_id,
    ]

    for fc in fc_list:
        assert demultiplex_context.housekeeper_api_.get_latest_bundle_version(fc)

    # WHEN starting post-processing for new demultiplexing from the CLI with dry run flag
    result: testing.Result = cli_runner.invoke(
        post_process_all_illumina_runs,
        ["--dry-run"],
        obj=demultiplex_context,
    )

    # THEN assert the command exits successfully
    assert result.exit_code == EXIT_SUCCESS


def test_finish_illumina_run_dry_run(
    caplog,
    cli_runner: testing.CliRunner,
    demultiplex_context: CGConfig,
    novaseq_6000_pre_1_5_kits_flow_cell_full_name: str,
):
    caplog.set_level(logging.INFO)

    # GIVEN a Illumina demultiplex-runs  finished output directory that exist

    # GIVEN a demultiplex context

    # GIVEN a run directory

    # WHEN starting post-processing for new demultiplexing from the CLI with dry run flag
    result: testing.Result = cli_runner.invoke(
        post_process_illumina_run,
        ["--dry-run", novaseq_6000_pre_1_5_kits_flow_cell_full_name],
        obj=demultiplex_context,
    )

    # THEN assert the command exits successfully
    assert result.exit_code == EXIT_SUCCESS
