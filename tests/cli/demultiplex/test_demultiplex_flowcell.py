"""Tests for running the demultiplex flowcell command"""
import logging
from pathlib import Path

from click import testing

from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.cli.demultiplex.demux import (
    delete_flow_cell,
    demultiplex_all,
    demultiplex_flow_cell,
)
from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.meta.demultiplex.housekeeper_storage_functions import (
    add_sample_sheet_path_to_housekeeper,
)
from cg.models.cg_config import CGConfig
from cg.models.flow_cell.flow_cell import FlowCellDirectoryData
from tests.meta.demultiplex.conftest import (
    tmp_flow_cell_demux_base_path,
    tmp_flow_cell_run_base_path,
)


def test_demultiplex_flow_cell_dry_run(
    cli_runner: testing.CliRunner,
    tmp_flow_cells_directory_ready_for_demultiplexing_bcl2fastq: Path,
    demultiplexing_context_for_demux: CGConfig,
    caplog,
):
    caplog.set_level(logging.INFO)

    # GIVEN that all files are present for demultiplexing
    flow_cell: FlowCellDirectoryData = FlowCellDirectoryData(
        tmp_flow_cells_directory_ready_for_demultiplexing_bcl2fastq
    )
    add_sample_sheet_path_to_housekeeper(
        flow_cell_directory=tmp_flow_cells_directory_ready_for_demultiplexing_bcl2fastq,
        flow_cell_name=flow_cell.id,
        hk_api=demultiplexing_context_for_demux.housekeeper_api,
    )

    # GIVEN an out dir that does not exist
    demux_api: DemultiplexingAPI = demultiplexing_context_for_demux.demultiplex_api
    assert demux_api.is_demultiplexing_possible(flow_cell=flow_cell)
    demux_dir: Path = demux_api.flow_cell_out_dir_path(flow_cell)
    unaligned_dir: Path = Path(demux_dir, DemultiplexingDirsAndFiles.UNALIGNED_DIR_NAME)
    assert demux_dir.exists() is False
    assert unaligned_dir.exists() is False

    # WHEN starting demultiplexing from the CLI with dry run flag
    result: testing.Result = cli_runner.invoke(
        demultiplex_flow_cell,
        [str(tmp_flow_cells_directory_ready_for_demultiplexing_bcl2fastq), "--dry-run"],
        obj=demultiplexing_context_for_demux,
    )

    # THEN assert the command exits without problems
    assert result.exit_code == 0

    # THEN assert no results folder was created since it is run in dry run mode
    assert demux_dir.exists() is False
    assert unaligned_dir.exists() is False


def test_demultiplex_bcl2fastq_flow_cell(
    cli_runner: testing.CliRunner,
    tmp_flow_cells_directory_ready_for_demultiplexing_bcl2fastq: Path,
    demultiplexing_context_for_demux: CGConfig,
    caplog,
    mocker,
):
    caplog.set_level(logging.INFO)

    # GIVEN that all files are present for bcl2fastq demultiplexing
    flow_cell: FlowCellDirectoryData = FlowCellDirectoryData(
        tmp_flow_cells_directory_ready_for_demultiplexing_bcl2fastq
    )
    add_sample_sheet_path_to_housekeeper(
        flow_cell_directory=tmp_flow_cells_directory_ready_for_demultiplexing_bcl2fastq,
        flow_cell_name=flow_cell.id,
        hk_api=demultiplexing_context_for_demux.housekeeper_api,
    )

    # GIVEN an out dir that does not exist
    demux_api: DemultiplexingAPI = demultiplexing_context_for_demux.demultiplex_api
    demux_dir: Path = demux_api.flow_cell_out_dir_path(flow_cell)
    unaligned_dir: Path = Path(demux_dir, DemultiplexingDirsAndFiles.UNALIGNED_DIR_NAME)
    assert demux_api.is_demultiplexing_possible(flow_cell=flow_cell)
    assert demux_dir.exists() is False
    assert unaligned_dir.exists() is False
    mocker.patch("cg.apps.tb.TrailblazerAPI.add_pending_analysis")

    # WHEN starting demultiplexing from the CLI with dry run flag
    result: testing.Result = cli_runner.invoke(
        demultiplex_flow_cell,
        [str(tmp_flow_cells_directory_ready_for_demultiplexing_bcl2fastq)],
        obj=demultiplexing_context_for_demux,
    )

    # THEN assert the command exits sucessfully

    assert result.exit_code == 0

    # THEN assert the results folder was created
    assert demux_dir.exists()
    assert unaligned_dir.exists()

    # THEN assert that the sbatch script was created
    assert demux_api.demultiplex_sbatch_path(flow_cell).exists()


def test_demultiplex_dragen_flowcell(
    cli_runner: testing.CliRunner,
    tmp_flow_cell_directory_bclconvert: Path,
    demultiplexing_context_for_demux: CGConfig,
    tmp_demultiplexed_runs_directory: Path,
    caplog,
    mocker,
):
    caplog.set_level(logging.INFO)

    # GIVEN that all files are present for Dragen demultiplexing

    flow_cell: FlowCellDirectoryData = FlowCellDirectoryData(
        flow_cell_path=tmp_flow_cell_directory_bclconvert, bcl_converter="dragen"
    )
    add_sample_sheet_path_to_housekeeper(
        flow_cell_directory=tmp_flow_cell_directory_bclconvert,
        flow_cell_name=flow_cell.id,
        hk_api=demultiplexing_context_for_demux.housekeeper_api,
    )

    # GIVEN an out dir that does not exist
    demux_api: DemultiplexingAPI = demultiplexing_context_for_demux.demultiplex_api
    demux_dir: Path = demux_api.flow_cell_out_dir_path(flow_cell)
    assert demux_api.is_demultiplexing_possible(flow_cell=flow_cell)
    assert demux_dir.exists() is False
    mocker.patch("cg.apps.tb.TrailblazerAPI.add_pending_analysis")

    # WHEN starting demultiplexing from the CLI with dry run flag
    result: testing.Result = cli_runner.invoke(
        demultiplex_flow_cell,
        [str(tmp_flow_cell_directory_bclconvert), "-b", "dragen"],
        obj=demultiplexing_context_for_demux,
    )

    # THEN assert the command exits without problems
    assert result.exit_code == 0

    # THEN assert the results folder was created
    assert demux_dir.exists()

    # THEN assert that the sbatch script was created
    assert demux_api.demultiplex_sbatch_path(flow_cell).exists()


def test_demultiplex_all_novaseq(
    cli_runner: testing.CliRunner,
    demultiplexing_context_for_demux: CGConfig,
    tmp_flow_cells_demux_all_directory: Path,
    caplog,
):
    """Test the demultiplex-all command on a directory with newly sequenced NovaSeq6000 flow cells."""
    caplog.set_level(logging.INFO)

    # GIVEN a demultiplexing context with an API and correct structure
    demux_api: DemultiplexingAPI = demultiplexing_context_for_demux.demultiplex_api
    assert demux_api.flow_cells_dir == tmp_flow_cells_demux_all_directory

    # GIVEN sequenced flow cells with their sample sheet in Housekeeper
    for flow_cell_dir in tmp_flow_cells_demux_all_directory.iterdir():
        flow_cell: FlowCellDirectoryData = FlowCellDirectoryData(flow_cell_path=flow_cell_dir)
        add_sample_sheet_path_to_housekeeper(
            flow_cell_directory=flow_cell_dir,
            flow_cell_name=flow_cell.id,
            hk_api=demultiplexing_context_for_demux.housekeeper_api,
        )
        assert demultiplexing_context_for_demux.housekeeper_api.last_version(bundle=flow_cell.id)

    # WHEN running the demultiplex all command
    result: testing.Result = cli_runner.invoke(
        demultiplex_all,
        ["--flow-cells-directory", str(demux_api.flow_cells_dir), "--dry-run"],
        obj=demultiplexing_context_for_demux,
    )

    # THEN assert it exits without problems
    assert result.exit_code == 0

    # THEN assert it found the directory
    assert "Found directory" in caplog.text

    # THEN assert it found a flow cell that is ready for demultiplexing
    assert f"Flow cell {flow_cell.id} is ready for downstream processing" in caplog.text


def test_is_demultiplexing_complete(tmp_flow_cell_directory_bcl2fastq: Path):
    """Tests the is_demultiplexing_complete property of FlowCellDirectoryData."""

    # GIVEN a demultiplexing directory with no demuxcomplete.txt file
    flow_cell: FlowCellDirectoryData = FlowCellDirectoryData(
        flow_cell_path=tmp_flow_cell_directory_bcl2fastq
    )
    assert not flow_cell.is_demultiplexing_complete

    # WHEN creating the demuxcomplete.txt file
    Path(flow_cell.path, DemultiplexingDirsAndFiles.DEMUX_COMPLETE).touch()

    # THEN the property should return true
    assert flow_cell.is_demultiplexing_complete


def test_delete_flow_cell_dry_run_status_db(
    cli_runner: testing.CliRunner,
    tmp_flow_cell_directory_bcl2fastq: Path,
    demultiplex_context: CGConfig,
    tmp_flow_cell_demux_base_path: Path,
    tmp_flow_cell_run_base_path: Path,
    bcl2fastq_flow_cell_id: str,
    caplog,
):
    """Test if logic work - call all true if status_db passed."""
    caplog.set_level(logging.DEBUG)

    demultiplex_context.demultiplex_api.flow_cells_dir = tmp_flow_cell_run_base_path
    demultiplex_context.demultiplex_api.demultiplexed_runs_dir = tmp_flow_cell_demux_base_path
    Path(tmp_flow_cell_run_base_path, f"some_prefix_1100_{bcl2fastq_flow_cell_id}").mkdir(
        parents=True, exist_ok=True
    )
    Path(tmp_flow_cell_demux_base_path, f"some_prefix_1100_{bcl2fastq_flow_cell_id}").mkdir(
        parents=True, exist_ok=True
    )
    # GIVEN a flow cell to be deleted
    assert bcl2fastq_flow_cell_id in tmp_flow_cell_directory_bcl2fastq.name

    # WHEN deleting a flowcell from status db in dry run mode
    result: testing.Result = cli_runner.invoke(
        delete_flow_cell,
        [
            "-f",
            bcl2fastq_flow_cell_id,
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
        f"DeleteDemuxAPI-Housekeeper: Would delete sample sheet files with tag {bcl2fastq_flow_cell_id}"
        in caplog.text
    )
    assert (
        f"DeleteDemuxAPI-Housekeeper: Would delete fastq and spring files related to flow cell {bcl2fastq_flow_cell_id}"
        in caplog.text
    )
    assert f"DeleteDemuxAPI-StatusDB: Would remove {bcl2fastq_flow_cell_id}" in caplog.text

    assert (
        "DeleteDemuxAPI-Hasta: Would have removed the following directory: "
        f"{demultiplex_context.demultiplex_api.demultiplexed_runs_dir / Path(f'some_prefix_1100_{bcl2fastq_flow_cell_id}')}\n"
        f"DeleteDemuxAPI-Hasta: Would have removed the following directory: {demultiplex_context.demultiplex_api.flow_cells_dir / Path(f'some_prefix_1100_{bcl2fastq_flow_cell_id}')}"
    ) in caplog.text
    assert "DeleteDemuxAPI-Init-files: Would have removed" not in caplog.text
