"""Tests for running the demultiplex flowcell command"""
import logging
from pathlib import Path
from typing import Dict

from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.cli.demultiplex.demux import demultiplex_flowcell
from cg.models.cg_config import CGConfig
from cg.models.demultiplex.flowcell import Flowcell
from click import testing


def test_demultiplex_flowcell_dry_run(
    cli_runner: testing.CliRunner,
    demultiplex_ready_flowcell: Path,
    demultiplex_context: CGConfig,
    caplog,
):
    caplog.set_level(logging.INFO)
    # GIVEN that all files are present for demultiplexing
    flowcell: Flowcell = Flowcell(demultiplex_ready_flowcell)
    # GIVEN a out dir that does not exist
    demux_api: DemultiplexingAPI = demultiplex_context.demultiplex_api
    assert demux_api.is_demultiplexing_possible(flowcell=flowcell)
    demux_dir: Path = demux_api.flowcell_out_dir_path(flowcell)
    unaligned_dir: Path = demux_dir / "Unaligned"
    assert demux_dir.exists() is False
    assert unaligned_dir.exists() is False

    # WHEN starting demultiplexing from the CLI with dry run flag
    result: testing.Result = cli_runner.invoke(
        demultiplex_flowcell,
        [str(demultiplex_ready_flowcell), "--dry-run"],
        obj=demultiplex_context,
    )
    # THEN assert the command exits without problems
    assert result.exit_code == 0
    # THEN assert no results folder was created since it is run in dry run mode
    assert demux_dir.exists() is False
    assert unaligned_dir.exists() is False


def test_demultiplex_flowcell(
    cli_runner: testing.CliRunner,
    demultiplex_ready_flowcell: Path,
    demultiplex_context: CGConfig,
    caplog,
):
    caplog.set_level(logging.INFO)
    # GIVEN that all files are present for demultiplexing
    flowcell: Flowcell = Flowcell(demultiplex_ready_flowcell)
    # GIVEN a out dir that does not exist
    demux_api: DemultiplexingAPI = demultiplex_context.demultiplex_api
    demux_dir: Path = demux_api.flowcell_out_dir_path(flowcell)
    unaligned_dir: Path = demux_dir / "Unaligned"
    assert demux_api.is_demultiplexing_possible(flowcell=flowcell)
    assert demux_dir.exists() is False
    assert unaligned_dir.exists() is False

    # WHEN starting demultiplexing from the CLI with dry run flag
    result: testing.Result = cli_runner.invoke(
        demultiplex_flowcell,
        [str(demultiplex_ready_flowcell)],
        obj=demultiplex_context,
    )
    # THEN assert the command exits without problems
    assert result.exit_code == 0
    # THEN assert the results folder was created
    assert demux_dir.exists()
    assert unaligned_dir.exists()
    # THEN assert that the sbatch script was created
    assert demux_api.demultiplex_sbatch_path(flowcell).exists()


def test_start_demultiplexing_when_already_completed(
    cli_runner: testing.CliRunner,
    demultiplex_ready_flowcell: Path,
    demultiplex_context: CGConfig,
    caplog,
):
    caplog.set_level(logging.DEBUG)
    # GIVEN that all files are present for demultiplexing
    flowcell: Flowcell = Flowcell(demultiplex_ready_flowcell)
    demux_api: DemultiplexingAPI = demultiplex_context.demultiplex_api
    # GIVEN that demultiplexing has started
    flowcell.demultiplexing_started_path.touch()
    # GIVEN a out dir that exist
    demux_api.flowcell_out_dir_path(flowcell).mkdir(parents=True)
    # GIVEN that demultiplexing is completed
    demux_api.demultiplexing_completed_path(flowcell=flowcell).touch()

    # WHEN starting demultiplexing from the CLI
    result: testing.Result = cli_runner.invoke(
        demultiplex_flowcell,
        [str(demultiplex_ready_flowcell)],
        obj=demultiplex_context,
    )
    # THEN assert the command exits without problems
    assert result.exit_code == 0
    # THEN assert it was communicated that demultiplexing was completed
    assert f"Demultiplexing is already completed for flowcell {flowcell.flowcell_id}"
