"""Tests for running the demultiplex flowcell command"""
import logging
from pathlib import Path

from click import testing

from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.cli.demultiplex.demux import demultiplex_all, demultiplex_flowcell, delete_flow_cell
from cg.models.cg_config import CGConfig
from cg.models.demultiplex.flowcell import Flowcell


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
    mocker,
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
    mocker.patch("cg.apps.tb.TrailblazerAPI.add_pending_analysis")

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


def test_demultiplex_bcl2fastq_flowcell(
    cli_runner: testing.CliRunner,
    demultiplex_ready_flowcell_bcl2fastq: Path,
    demultiplex_context: CGConfig,
    caplog,
    mocker,
):
    caplog.set_level(logging.INFO)

    # GIVEN that all files are present for bcl2fastq demultiplexing
    flowcell: Flowcell = Flowcell(demultiplex_ready_flowcell_bcl2fastq)

    # GIVEN a out dir that does not exist
    demux_api: DemultiplexingAPI = demultiplex_context.demultiplex_api
    demux_dir: Path = demux_api.flowcell_out_dir_path(flowcell)
    unaligned_dir: Path = demux_dir / "Unaligned"
    assert demux_api.is_demultiplexing_possible(flowcell=flowcell)
    assert demux_dir.exists() is False
    assert unaligned_dir.exists() is False
    mocker.patch("cg.apps.tb.TrailblazerAPI.add_pending_analysis")

    # WHEN starting demultiplexing from the CLI with dry run flag
    result: testing.Result = cli_runner.invoke(
        demultiplex_flowcell,
        [str(demultiplex_ready_flowcell_bcl2fastq)],
        obj=demultiplex_context,
    )

    # THEN assert the command exits without problems
    assert result.exit_code == 0

    # THEN assert the results folder was created
    assert demux_dir.exists()
    assert unaligned_dir.exists()

    # THEN assert that the sbatch script was created
    assert demux_api.demultiplex_sbatch_path(flowcell).exists()


def test_demultiplex_dragen_flowcell(
    cli_runner: testing.CliRunner,
    demultiplex_ready_flowcell_dragen: Path,
    demultiplex_context: CGConfig,
    demultiplexed_flowcells_working_directory: Path,
    caplog,
    mocker,
):
    caplog.set_level(logging.INFO)

    # GIVEN that all files are present for dragen demultiplexing
    flowcell: Flowcell = Flowcell(
        flowcell_path=demultiplex_ready_flowcell_dragen, bcl_converter="dragen"
    )

    # GIVEN a out dir that does not exist
    demux_api: DemultiplexingAPI = demultiplex_context.demultiplex_api
    demux_dir: Path = demux_api.flowcell_out_dir_path(flowcell)
    unaligned_dir: Path = demux_dir / "Unaligned"
    assert demux_api.is_demultiplexing_possible(flowcell=flowcell)
    assert demux_dir.exists() is False
    assert unaligned_dir.exists() is False
    mocker.patch("cg.apps.tb.TrailblazerAPI.add_pending_analysis")

    # WHEN starting demultiplexing from the CLI with dry run flag
    result: testing.Result = cli_runner.invoke(
        demultiplex_flowcell,
        [str(demultiplex_ready_flowcell_dragen), "-b", "dragen"],
        obj=demultiplex_context,
    )

    # THEN assert the command exits without problems
    assert result.exit_code == 0

    # THEN assert the results folder was created
    assert demux_dir.exists()
    assert unaligned_dir.exists()

    # THEN assert that the sbatch script was created
    assert demux_api.demultiplex_sbatch_path(flowcell).exists()


def test_demultiplex_all(
    cli_runner: testing.CliRunner,
    demultiplex_context: CGConfig,
    demultiplex_ready_flowcell: Path,
    caplog,
    mocker,
):
    caplog.set_level(logging.INFO)

    # GIVEN a context with the path to a directory where at least one flowcell is ready for demux
    demux_api: DemultiplexingAPI = demultiplex_context.demultiplex_api
    flowcell_object: Flowcell = Flowcell(flowcell_path=demultiplex_ready_flowcell)

    assert demux_api.run_dir == demultiplex_ready_flowcell.parent

    # WHEN running the demultiplex all command
    result: testing.Result = cli_runner.invoke(
        demultiplex_all, ["--dry-run"], obj=demultiplex_context
    )

    # THEN assert it exits without problems
    assert result.exit_code == 0

    # THEN assert it found the directory
    assert "Found directory" in caplog.text

    # THEN assert it found a flowcell that is ready for demultiplexing
    assert f"Flowcell {flowcell_object.flowcell_id} is ready for demultiplexing" in caplog.text


def test_start_demultiplexing_when_already_completed(
    cli_runner: testing.CliRunner,
    demultiplex_ready_flowcell: Path,
    demultiplex_context: CGConfig,
    caplog,
    mocker,
):
    caplog.set_level(logging.DEBUG)

    # GIVEN that all files are present for demultiplexing
    # flowcell: Flowcell = Flowcell(demultiplex_ready_flowcell_dragen, bcl_converter="dragen")
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
        [str(demultiplex_ready_flowcell), "-b", "bcl2fastq"],
        obj=demultiplex_context,
    )

    # THEN assert the command exits without problems
    assert result.exit_code == 0

    # THEN assert it was communicated that demultiplexing was completed
    assert f"Demultiplexing is already completed for flowcell {flowcell.flowcell_id}"


def test_delete_flow_cell_dry_run_cgstats(
    cli_runner: testing.CliRunner,
    demultiplex_ready_flowcell: Path,
    demultiplex_context: CGConfig,
    flowcell_name: str,
    caplog,
):
    """Test if logic work - call function in dry run"""
    caplog.set_level(logging.DEBUG)

    # GIVEN a flow cell to be deleted
    flow_cell_name: str = flowcell_name
    assert flow_cell_name in demultiplex_ready_flowcell.name

    # WHEN executing the commando to remove flow cell from cgstats in dry run mode
    result: testing.Result = cli_runner.invoke(
        delete_flow_cell,
        [
            "-d",
            str(demultiplex_context.demultiplex_api.out_dir),
            "-r",
            demultiplex_ready_flowcell,
            "--cg-stats",
            "--dry-run",
            "--yes",
        ],
        obj=demultiplex_context,
    )

    # THEN the exit code should be fine
    assert result.exit_code == 0

    # THEN the approriate flow cell should be prompted for removal
    assert f"DeleteDemuxAPI-CGStats: Would remove {flow_cell_name}" in caplog.text


def test_delete_flow_cell_dry_run_status_db(
    cli_runner: testing.CliRunner,
    demultiplex_ready_flowcell: Path,
    demultiplex_context: CGConfig,
    flowcell_full_name: str,
    flowcell_name: str,
    caplog,
):
    """Test if logic work - call all true if status_db passed"""
    caplog.set_level(logging.DEBUG)

    # GIVEN a flow cell to be deleted

    flow_cell_name: str = flowcell_name
    assert flow_cell_name in demultiplex_ready_flowcell.name

    # WHEN deleting a flowcell from status db in dry run mode
    result: testing.Result = cli_runner.invoke(
        delete_flow_cell,
        [
            "-d",
            str(demultiplex_context.demultiplex_api.out_dir),
            "-r",
            demultiplex_ready_flowcell,
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
        f"DeleteDemuxAPI-Housekeeper: Would delete sample sheet files with tag {flow_cell_name}"
        in caplog.text
    )
    assert (
        f"DeleteDemuxAPI-Housekeeper: Would delete fastq and spring files related to flowcell {flow_cell_name}"
        in caplog.text
    )
    assert f"DeleteDemuxAPI-StatusDB: Would remove {flow_cell_name}" in caplog.text
    assert f"DeleteDemuxAPI-CGStats: Would remove {flow_cell_name}" in caplog.text
    assert (
        "DeleteDemuxAPI-Hasta: Would have removed the following directory: "
        f"{demultiplex_context.demultiplex_api.out_dir / Path(flowcell_full_name)}\n"
        f"DeleteDemuxAPI-Hasta: Would have removed the following directory: {demultiplex_ready_flowcell}"
    ) in caplog.text
    assert "DeleteDemuxAPI-Init-files: Would have removed" not in caplog.text
