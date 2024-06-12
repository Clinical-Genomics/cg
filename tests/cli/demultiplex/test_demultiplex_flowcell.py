"""Tests for running the demultiplex flowcell command"""

import logging
from pathlib import Path

from click import testing

from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.cli.demultiplex.demux import demultiplex_all, demultiplex_sequencing_run
from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.meta.demultiplex.housekeeper_storage_functions import (
    add_and_include_sample_sheet_path_to_housekeeper,
)
from cg.models.cg_config import CGConfig
from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData


def test_demultiplex_dragen_flowcell(
    cli_runner: testing.CliRunner,
    tmp_flow_cell_directory_bcl_convert: Path,
    demultiplexing_context_for_demux: CGConfig,
    caplog,
    mocker,
):
    caplog.set_level(logging.INFO)

    # GIVEN that all files are present for Dragen demultiplexing

    flow_cell = IlluminaRunDirectoryData(tmp_flow_cell_directory_bcl_convert)
    add_and_include_sample_sheet_path_to_housekeeper(
        flow_cell_directory=tmp_flow_cell_directory_bcl_convert,
        flow_cell_name=flow_cell.id,
        hk_api=demultiplexing_context_for_demux.housekeeper_api,
    )

    # GIVEN a flow cell that is ready for demultiplexing
    demux_api: DemultiplexingAPI = demultiplexing_context_for_demux.demultiplex_api
    demux_dir: Path = demux_api.demultiplexed_run_dir_path(flow_cell)
    assert demux_api.is_demultiplexing_possible(sequencing_run=flow_cell)
    mocker.patch("cg.apps.tb.TrailblazerAPI.add_pending_analysis")

    # GIVEN an already existing output directory
    demux_dir.mkdir(parents=True)
    marker_file = Path(demux_dir, "dummy_file_present_in_old_dir")
    marker_file.touch()
    assert marker_file.exists()

    # WHEN starting demultiplexing from the CLI
    result: testing.Result = cli_runner.invoke(
        demultiplex_sequencing_run,
        [str(tmp_flow_cell_directory_bcl_convert)],
        obj=demultiplexing_context_for_demux,
    )

    # THEN assert the command exits without problems
    assert result.exit_code == 0

    # THEN assert the results folder was created
    assert demux_dir.exists()

    # THEN assert that the old directory was removed
    assert not marker_file.exists()

    # THEN assert that the sbatch script was created
    assert demux_api.demultiplex_sbatch_path(flow_cell).exists()


def test_demultiplex_all_novaseq(
    cli_runner: testing.CliRunner,
    demultiplexing_context_for_demux: CGConfig,
    tmp_illumina_flow_cells_demux_all_directory,
    caplog,
):
    """Test the demultiplex-all command on a directory with newly sequenced NovaSeq6000 sequencing runs."""
    caplog.set_level(logging.INFO)

    # GIVEN a demultiplexing context with an API and correct structure
    demux_api: DemultiplexingAPI = demultiplexing_context_for_demux.demultiplex_api
    assert demux_api.sequencing_runs_dir == tmp_illumina_flow_cells_demux_all_directory

    # GIVEN a sequencing run with their sample sheet in Housekeeper
    for sequencing_run_dir in tmp_illumina_flow_cells_demux_all_directory.iterdir():
        sequencing_run: IlluminaRunDirectoryData = IlluminaRunDirectoryData(
            sequencing_run_path=sequencing_run_dir
        )
        add_and_include_sample_sheet_path_to_housekeeper(
            flow_cell_directory=sequencing_run_dir,
            flow_cell_name=sequencing_run.id,
            hk_api=demultiplexing_context_for_demux.housekeeper_api,
        )
        assert demultiplexing_context_for_demux.housekeeper_api.last_version(
            bundle=sequencing_run.id
        )

    # WHEN running the demultiplex all command
    result: testing.Result = cli_runner.invoke(
        demultiplex_all,
        ["--sequencing-runs-directory", str(demux_api.sequencing_runs_dir), "--dry-run"],
        obj=demultiplexing_context_for_demux,
    )

    # THEN assert it exits without problems
    assert result.exit_code == 0

    # THEN assert it found the directory
    assert "Found directory" in caplog.text

    # THEN assert it found a flow cell that is ready for demultiplexing
    assert f"Sequencing run {sequencing_run.id} is ready for downstream processing" in caplog.text


def test_is_demultiplexing_complete(
    hiseq_x_single_index_demultiplexed_flow_cell_with_sample_sheet: IlluminaRunDirectoryData,
):
    """Tests the is_demultiplexing_complete property of IlluminaRunDirectoryData."""

    # GIVEN a demultiplexing directory with a demuxcomplete.txt file
    assert Path(
        hiseq_x_single_index_demultiplexed_flow_cell_with_sample_sheet.path,
        DemultiplexingDirsAndFiles.DEMUX_COMPLETE,
    ).exists()

    # WHEN checking if the demultiplexing is complete

    # THEN the property should return true
    assert hiseq_x_single_index_demultiplexed_flow_cell_with_sample_sheet.is_demultiplexing_complete


def test_is_demultiplexing_not_complete(
    hiseq_2500_dual_index_demux_runs_flow_cell: IlluminaRunDirectoryData,
):
    """Tests the is_demultiplexing_complete property of IlluminaRunDirectoryData."""

    # GIVEN a demultiplexing directory with a demuxcomplete.txt file
    assert not Path(
        hiseq_2500_dual_index_demux_runs_flow_cell.path,
        DemultiplexingDirsAndFiles.DEMUX_COMPLETE,
    ).exists()

    # WHEN checking if the demultiplexing is complete

    # THEN the property should return true
    assert not hiseq_2500_dual_index_demux_runs_flow_cell.is_demultiplexing_complete
