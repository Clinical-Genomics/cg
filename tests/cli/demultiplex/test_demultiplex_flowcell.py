"""Tests for running the demultiplex flowcell command"""
import logging
from pathlib import Path

from click import testing

from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.cli.demultiplex.demux import demultiplex_all, demultiplex_flow_cell, delete_flow_cell
from cg.models.cg_config import CGConfig
from cg.models.demultiplex.flow_cell import FlowCell


def test_demultiplex_flow_cell_dry_run(
    cli_runner: testing.CliRunner,
    demultiplex_ready_flow_cell: Path,
    demultiplex_context: CGConfig,
    caplog,
):
    caplog.set_level(logging.INFO)

    # GIVEN that all files are present for demultiplexing
    flow_cell: FlowCell = FlowCell(demultiplex_ready_flow_cell)

    # GIVEN a out dir that does not exist
    demux_api: DemultiplexingAPI = demultiplex_context.demultiplex_api
    assert demux_api.is_demultiplexing_possible(flow_cell=flow_cell)
    demux_dir: Path = demux_api.flow_cell_out_dir_path(flow_cell)
    unaligned_dir: Path = demux_dir / "Unaligned"
    assert demux_dir.exists() is False
    assert unaligned_dir.exists() is False

    # WHEN starting demultiplexing from the CLI with dry run flag
    result: testing.Result = cli_runner.invoke(
        demultiplex_flow_cell,
        [str(demultiplex_ready_flow_cell), "--dry-run"],
        obj=demultiplex_context,
    )

    # THEN assert the command exits without problems
    assert result.exit_code == 0

    # THEN assert no results folder was created since it is run in dry run mode
    assert demux_dir.exists() is False
    assert unaligned_dir.exists() is False


def test_demultiplex_flow_cell(
    cli_runner: testing.CliRunner,
    demultiplex_ready_flow_cell: Path,
    demultiplex_context: CGConfig,
    caplog,
    mocker,
):
    caplog.set_level(logging.INFO)

    # GIVEN that all files are present for demultiplexing
    flow_cell: FlowCell = FlowCell(demultiplex_ready_flow_cell)

    # GIVEN a out dir that does not exist
    demux_api: DemultiplexingAPI = demultiplex_context.demultiplex_api
    demux_dir: Path = demux_api.flow_cell_out_dir_path(flow_cell)
    unaligned_dir: Path = demux_dir / "Unaligned"
    assert demux_api.is_demultiplexing_possible(flow_cell=flow_cell)
    assert demux_dir.exists() is False
    assert unaligned_dir.exists() is False
    mocker.patch("cg.apps.tb.TrailblazerAPI.add_pending_analysis")

    # WHEN starting demultiplexing from the CLI with dry run flag
    result: testing.Result = cli_runner.invoke(
        demultiplex_flow_cell,
        [str(demultiplex_ready_flow_cell)],
        obj=demultiplex_context,
    )

    # THEN assert the command exits without problems
    assert result.exit_code == 0

    # THEN assert the results folder was created
    assert demux_dir.exists()
    assert unaligned_dir.exists()

    # THEN assert that the sbatch script was created
    assert demux_api.demultiplex_sbatch_path(flow_cell).exists()


def test_demultiplex_bcl2fastq_flowcell(
    cli_runner: testing.CliRunner,
    demultiplex_ready_flow_cell_bcl2fastq: Path,
    demultiplex_context: CGConfig,
    caplog,
    mocker,
):
    caplog.set_level(logging.INFO)

    # GIVEN that all files are present for bcl2fastq demultiplexing
    flow_cell: FlowCell = FlowCell(demultiplex_ready_flow_cell_bcl2fastq)

    # GIVEN a out dir that does not exist
    demux_api: DemultiplexingAPI = demultiplex_context.demultiplex_api
    demux_dir: Path = demux_api.flow_cell_out_dir_path(flow_cell)
    unaligned_dir: Path = demux_dir / "Unaligned"
    assert demux_api.is_demultiplexing_possible(flow_cell=flow_cell)
    assert demux_dir.exists() is False
    assert unaligned_dir.exists() is False
    mocker.patch("cg.apps.tb.TrailblazerAPI.add_pending_analysis")

    # WHEN starting demultiplexing from the CLI with dry run flag
    result: testing.Result = cli_runner.invoke(
        demultiplex_flow_cell,
        [str(demultiplex_ready_flow_cell_bcl2fastq)],
        obj=demultiplex_context,
    )

    # THEN assert the command exits without problems
    assert result.exit_code == 0

    # THEN assert the results folder was created
    assert demux_dir.exists()
    assert unaligned_dir.exists()

    # THEN assert that the sbatch script was created
    assert demux_api.demultiplex_sbatch_path(flow_cell).exists()


def test_demultiplex_dragen_flowcell(
    cli_runner: testing.CliRunner,
    demultiplex_ready_flow_cell_dragen: Path,
    demultiplex_context: CGConfig,
    demultiplexed_flow_cells_working_directory: Path,
    caplog,
    mocker,
):
    caplog.set_level(logging.INFO)

    # GIVEN that all files are present for dragen demultiplexing
    flow_cell: FlowCell = FlowCell(
        flow_cell_path=demultiplex_ready_flow_cell_dragen, bcl_converter="dragen"
    )

    # GIVEN a out dir that does not exist
    demux_api: DemultiplexingAPI = demultiplex_context.demultiplex_api
    demux_dir: Path = demux_api.flow_cell_out_dir_path(flow_cell)
    unaligned_dir: Path = demux_dir / "Unaligned"
    assert demux_api.is_demultiplexing_possible(flow_cell=flow_cell)
    assert demux_dir.exists() is False
    assert unaligned_dir.exists() is False
    mocker.patch("cg.apps.tb.TrailblazerAPI.add_pending_analysis")

    # WHEN starting demultiplexing from the CLI with dry run flag
    result: testing.Result = cli_runner.invoke(
        demultiplex_flow_cell,
        [str(demultiplex_ready_flow_cell_dragen), "-b", "dragen"],
        obj=demultiplex_context,
    )

    # THEN assert the command exits without problems
    assert result.exit_code == 0

    # THEN assert the results folder was created
    assert demux_dir.exists()
    assert unaligned_dir.exists()

    # THEN assert that the sbatch script was created
    assert demux_api.demultiplex_sbatch_path(flow_cell).exists()


def test_demultiplex_all(
    cli_runner: testing.CliRunner,
    demultiplex_context: CGConfig,
    demultiplex_ready_flow_cell: Path,
    caplog,
):
    caplog.set_level(logging.INFO)

    # GIVEN a context with the path to a directory where at least one flowcell is ready for demux
    demux_api: DemultiplexingAPI = demultiplex_context.demultiplex_api
    flow_cell: FlowCell = FlowCell(flow_cell_path=demultiplex_ready_flow_cell)

    assert demux_api.run_dir == demultiplex_ready_flow_cell.parent

    # WHEN running the demultiplex all command
    result: testing.Result = cli_runner.invoke(
        demultiplex_all, ["--dry-run"], obj=demultiplex_context
    )

    # THEN assert it exits without problems
    assert result.exit_code == 0

    # THEN assert it found the directory
    assert "Found directory" in caplog.text

    # THEN assert it found a flow cell that is ready for demultiplexing
    assert f"Flow cell {flow_cell.id} is ready for demultiplexing" in caplog.text


def test_start_demultiplex_flow_cell(
    caplog,
    cli_runner: testing.CliRunner,
    demultiplex_ready_flow_cell: Path,
    demultiplex_context: CGConfig,
    flow_cell: FlowCell,
    mocker,
):
    caplog.set_level(logging.DEBUG)

    # GIVEN that all files are present for demultiplexing
    demux_api: DemultiplexingAPI = demultiplex_context.demultiplex_api

    # GIVEN that demultiplexing has started
    flow_cell.demultiplexing_started_path.touch()

    # GIVEN a out dir that exist
    demux_api.flow_cell_out_dir_path(flow_cell).mkdir(parents=True)

    # GIVEN that demultiplexing is completed
    demux_api.demultiplexing_completed_path(flow_cell=flow_cell).touch()

    mocker.patch("cg.apps.tb.TrailblazerAPI.add_pending_analysis")

    # WHEN starting demultiplexing from the CLI
    result: testing.Result = cli_runner.invoke(
        demultiplex_flow_cell,
        [str(demultiplex_ready_flow_cell), "-b", "bcl2fastq"],
        obj=demultiplex_context,
    )

    # THEN assert the command exits without problems
    assert result.exit_code == 0

    # THEN assert it was communicated that previous demux was deleted
    assert f"Removing flow cell demultiplexing directory {flow_cell.path}"

    # THEN demultiplexing was started
    assert f"Demultiplexing running as job" in caplog.text


def test_delete_flow_cell_dry_run_cgstats(
    cli_runner: testing.CliRunner,
    demultiplex_ready_flow_cell: Path,
    demultiplex_context: CGConfig,
    flow_cell_id: str,
    caplog,
):
    """Test if logic work - call function in dry run."""
    caplog.set_level(logging.DEBUG)

    # GIVEN a flow cell to be deleted
    assert flow_cell_id in demultiplex_ready_flow_cell.name

    # WHEN executing the commando to remove flow cell from cgstats in dry run mode
    result: testing.Result = cli_runner.invoke(
        delete_flow_cell,
        [
            "-d",
            str(demultiplex_context.demultiplex_api.out_dir),
            "-r",
            demultiplex_ready_flow_cell,
            "--cg-stats",
            "--dry-run",
            "--yes",
        ],
        obj=demultiplex_context,
    )

    # THEN the exit code should be fine
    assert result.exit_code == 0

    # THEN the appropriate flow cell should be prompted for removal
    assert f"DeleteDemuxAPI-CGStats: Would remove {flow_cell_id}" in caplog.text


def test_delete_flow_cell_dry_run_status_db(
    cli_runner: testing.CliRunner,
    demultiplex_ready_flow_cell: Path,
    demultiplex_context: CGConfig,
    flow_cell_full_name: str,
    flow_cell_id: str,
    caplog,
):
    """Test if logic work - call all true if status_db passed."""
    caplog.set_level(logging.DEBUG)

    # GIVEN a flow cell to be deleted
    assert flow_cell_id in demultiplex_ready_flow_cell.name

    # WHEN deleting a flowcell from status db in dry run mode
    result: testing.Result = cli_runner.invoke(
        delete_flow_cell,
        [
            "-d",
            str(demultiplex_context.demultiplex_api.out_dir),
            "-r",
            demultiplex_ready_flow_cell,
            "--status-db",
            "--dry-run",
            "--yes",
        ],
        obj=demultiplex_context,
    )

    # THEN the code should be executed successfully
    assert result.exit_code == 0

    # THEN it should be notified that it was going to remove all but init-files
    assert (
        f"DeleteDemuxAPI-Housekeeper: Would delete sample sheet files with tag {flow_cell_id}"
        in caplog.text
    )
    assert (
        f"DeleteDemuxAPI-Housekeeper: Would delete fastq and spring files related to flow cell {flow_cell_id}"
        in caplog.text
    )
    assert f"DeleteDemuxAPI-StatusDB: Would remove {flow_cell_id}" in caplog.text
    assert f"DeleteDemuxAPI-CGStats: Would remove {flow_cell_id}" in caplog.text
    assert (
        "DeleteDemuxAPI-Hasta: Would have removed the following directory: "
        f"{demultiplex_context.demultiplex_api.out_dir / Path(flow_cell_full_name)}\n"
        f"DeleteDemuxAPI-Hasta: Would have removed the following directory: {demultiplex_ready_flow_cell}"
    ) in caplog.text
    assert "DeleteDemuxAPI-Init-files: Would have removed" not in caplog.text
