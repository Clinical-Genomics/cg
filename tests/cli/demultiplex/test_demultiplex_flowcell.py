"""Tests for running the demultiplex flowcell command"""
import logging
from pathlib import Path
from typing import Dict

from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.apps.demultiplex.flowcell import Flowcell
from cg.cli.demultiplex.base import demultiplex_flowcell
from click import testing


def test_demultiplex_flowcell_dry_run(
    cli_runner: testing.CliRunner,
    demultiplex_ready_flowcell: Path,
    demultiplex_context: Dict[str, DemultiplexingAPI],
    caplog,
):
    caplog.set_level(logging.INFO)
    # GIVEN that all files are present for demultiplexing
    flowcell: Flowcell = Flowcell(demultiplex_ready_flowcell)
    assert flowcell.is_demultiplexing_possible()
    # GIVEN a out dir that does not exist
    demux_api: DemultiplexingAPI = demultiplex_context["demultiplex_api"]
    assert demux_api.flowcell_out_dir_path(flowcell).exists() is False

    # WHEN starting demultiplexing from the CLI with dry run flag
    result: testing.Result = cli_runner.invoke(
        demultiplex_flowcell,
        [str(demultiplex_ready_flowcell), "--dry-run"],
        obj=demultiplex_context,
    )
    # THEN assert the command exits without problems
    assert result.exit_code == 0
    # THEN assert no results folder was created since it is run in dry run mode
    assert demux_api.flowcell_out_dir_path(flowcell).exists() is False


def test_demultiplex_flowcell(
    cli_runner: testing.CliRunner,
    demultiplex_ready_flowcell: Path,
    demultiplex_context: Dict[str, DemultiplexingAPI],
    caplog,
):
    caplog.set_level(logging.INFO)
    # GIVEN that all files are present for demultiplexing
    flowcell: Flowcell = Flowcell(demultiplex_ready_flowcell)
    assert flowcell.is_demultiplexing_possible()
    # GIVEN a out dir that does not exist
    demux_api: DemultiplexingAPI = demultiplex_context["demultiplex_api"]
    assert demux_api.flowcell_out_dir_path(flowcell).exists() is False

    # WHEN starting demultiplexing from the CLI with dry run flag
    result: testing.Result = cli_runner.invoke(
        demultiplex_flowcell,
        [str(demultiplex_ready_flowcell)],
        obj=demultiplex_context,
    )
    # THEN assert the command exits without problems
    assert result.exit_code == 0
    # THEN assert the results folder was created
    assert demux_api.flowcell_out_dir_path(flowcell).exists()
    # THEN assert that the sbatch script was created
    assert demux_api.demultiplex_sbatch_path(flowcell).exists()
