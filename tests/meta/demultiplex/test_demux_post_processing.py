import logging
from pathlib import Path

from cg.constants.demultiplexing import DemultiplexingDirsAndFiles, BclConverter
from cg.meta.demultiplex.demux_post_processing import (
    DemuxPostProcessingAPI,
    DemuxPostProcessingHiseqXAPI,
)
from cg.models.cg_config import CGConfig
from cg.models.demultiplex.flowcell import Flowcell


def test_set_dry_run(
    demultiplex_context: CGConfig,
):
    # GIVEN a demultiplex context

    # GIVEN a Demultiplexing post process API
    post_demux_api: DemuxPostProcessingAPI = DemuxPostProcessingAPI(config=demultiplex_context)

    # THEN dry run should be False
    assert post_demux_api.dry_run is False

    # WHEN dry run set to True
    post_demux_api.set_dry_run(dry_run=True)

    # THEN dry run should be True
    assert post_demux_api.dry_run is True


def test_cg_transfer_flow_cell(
    caplog,
    demultiplexed_flowcell_working_directory: Path,
    demultiplex_context: CGConfig,
    flowcell_object: Flowcell,
):
    caplog.set_level(logging.INFO)

    # GIVEN a demultiplex context

    # GIVEN a Demultiplexing post process API
    post_demux_api: DemuxPostProcessingHiseqXAPI = DemuxPostProcessingHiseqXAPI(
        config=demultiplex_context
    )

    # When adding to cgstats
    post_demux_api.cg_transfer_flow_cell(flowcell_name=flowcell_object.flowcell_full_name)

    # THEN we should run the command
    assert f"transfer {flowcell_object.flowcell_full_name}" in caplog.text


def test_add_to_cgstats(
    caplog,
    demultiplexed_flowcell_working_directory: Path,
    demultiplex_context: CGConfig,
    flowcell_object: Flowcell,
):
    caplog.set_level(logging.INFO)

    # GIVEN a demultiplex context

    # GIVEN a Demultiplexing post process API
    post_demux_api: DemuxPostProcessingHiseqXAPI = DemuxPostProcessingHiseqXAPI(
        config=demultiplex_context
    )

    # When adding to cgstats
    post_demux_api.add_to_cgstats(flowcell_path=flowcell_object.path)

    # THEN we should run the command
    assert f"add --machine X {flowcell_object.path}" in caplog.text


def test_cgstats_select_project(
    caplog,
    demultiplexed_flowcell_working_directory: Path,
    demultiplex_context: CGConfig,
    flowcell_object: Flowcell,
    flowcell_project_id: int,
):
    caplog.set_level(logging.INFO)

    # GIVEN a demultiplex context

    # GIVEN a Demultiplexing post process API
    post_demux_api: DemuxPostProcessingHiseqXAPI = DemuxPostProcessingHiseqXAPI(
        config=demultiplex_context
    )

    # GIVEN an unaligned project directory
    Path(flowcell_object.path, "Unaligned", f"Project_{flowcell_project_id}").mkdir(
        parents=True, exist_ok=True
    )

    # When adding to cgstats
    post_demux_api.cgstats_select_project(
        flowcell_name=flowcell_object.flowcell_full_name, flowcell_path=flowcell_object.path
    )

    expected_cgstats_select_project_log_file: Path = Path(
        flowcell_object.path,
        "-".join(["stats", str(flowcell_project_id), flowcell_object.flowcell_full_name]) + ".txt",
    )

    # THEN we should have created a stats outfile
    assert expected_cgstats_select_project_log_file.exists()

    # Clean up from calling cgstats_select_project
    expected_cgstats_select_project_log_file.unlink()

    # THEN we should run the command
    assert f"select --project {flowcell_project_id}" in caplog.text


def test_cgstats_lanestats(
    caplog,
    demultiplexed_flowcell_working_directory: Path,
    demultiplex_context: CGConfig,
    flowcell_object: Flowcell,
):
    caplog.set_level(logging.INFO)

    # GIVEN a demultiplex context

    # GIVEN a Demultiplexing post process API
    post_demux_api: DemuxPostProcessingHiseqXAPI = DemuxPostProcessingHiseqXAPI(
        config=demultiplex_context
    )

    # When adding to cgstats
    post_demux_api.cgstats_lanestats(flowcell_path=flowcell_object.path)

    # THEN we should run the command
    assert f"lanestats {flowcell_object.path}" in caplog.text


def test_post_process_flowcell_copy_not_completed(
    caplog,
    demultiplexed_flowcell_working_directory: Path,
    demultiplex_context: CGConfig,
    flowcell_object: Flowcell,
):
    caplog.set_level(logging.DEBUG)

    # GIVEN a demultiplex context

    # GIVEN a Demultiplexing post process API
    post_demux_api: DemuxPostProcessingHiseqXAPI = DemuxPostProcessingHiseqXAPI(
        config=demultiplex_context
    )

    # GIVEN a not completely copied flow cell
    copy_complete_file: Path = Path(
        flowcell_object.path, DemultiplexingDirsAndFiles.Hiseq_X_COPY_COMPLETE
    )
    if copy_complete_file.exists():
        copy_complete_file.unlink()

    # When post-processing flow cell
    post_demux_api.post_process_flowcell(
        flowcell=flowcell_object,
        flowcell_name=flowcell_object.flowcell_full_name,
        flowcell_path=flowcell_object.path,
    )

    # Reinstate
    Path(flowcell_object.path, DemultiplexingDirsAndFiles.Hiseq_X_COPY_COMPLETE).touch()

    # THEN we should run the command
    assert f"{flowcell_object.flowcell_full_name} is not yet completely copied" in caplog.text


def test_post_process_flowcell_delivery_started(
    caplog,
    demultiplexed_flowcell_working_directory: Path,
    demultiplex_context: CGConfig,
    flowcell_object: Flowcell,
):
    caplog.set_level(logging.DEBUG)

    # GIVEN a demultiplex context

    # GIVEN a Demultiplexing post process API
    post_demux_api: DemuxPostProcessingHiseqXAPI = DemuxPostProcessingHiseqXAPI(
        config=demultiplex_context
    )

    # GIVEN an already started flag file
    Path(flowcell_object.path, DemultiplexingDirsAndFiles.DELIVERY).touch()

    # When post-processing flow cell
    post_demux_api.post_process_flowcell(
        flowcell=flowcell_object,
        flowcell_name=flowcell_object.flowcell_full_name,
        flowcell_path=flowcell_object.path,
    )

    # Clean up
    Path(flowcell_object.path, DemultiplexingDirsAndFiles.DELIVERY).unlink()

    # THEN we should run the command
    assert (
        f"{flowcell_object.flowcell_full_name} copy is complete and delivery has already started"
        in caplog.text
    )


def test_post_process_flowcell_not_hiseq_x(
    caplog,
    demultiplexed_flowcell_working_directory: Path,
    demultiplex_context: CGConfig,
    flowcell_object: Flowcell,
):
    caplog.set_level(logging.DEBUG)

    # GIVEN a demultiplex context

    # GIVEN a Demultiplexing post process API
    post_demux_api: DemuxPostProcessingHiseqXAPI = DemuxPostProcessingHiseqXAPI(
        config=demultiplex_context
    )

    # GIVEN no hiseq X flow cell
    hiseq_x_dir: Path = Path(flowcell_object.path, DemultiplexingDirsAndFiles.HiseqX_TILE_DIR)
    if hiseq_x_dir.exists():
        hiseq_x_dir.rmdir()

    # When post-processing flow cell
    post_demux_api.post_process_flowcell(
        flowcell=flowcell_object,
        flowcell_name=flowcell_object.flowcell_full_name,
        flowcell_path=flowcell_object.path,
    )

    # THEN we should run the command
    assert f"{flowcell_object.flowcell_full_name} is not an Hiseq X flow cell" in caplog.text


def test_post_process_flowcell(
    caplog,
    demultiplexed_flowcell_working_directory: Path,
    demultiplex_context: CGConfig,
    flowcell_object: Flowcell,
    flowcell_project_id: int,
):
    caplog.set_level(logging.DEBUG)

    # GIVEN a demultiplex context

    # GIVEN a Demultiplexing post process API
    post_demux_api: DemuxPostProcessingHiseqXAPI = DemuxPostProcessingHiseqXAPI(
        config=demultiplex_context
    )

    # GIVEN a Hiseq X tile directory
    hiseq_x_tile_dir: Path = Path(flowcell_object.path, DemultiplexingDirsAndFiles.HiseqX_TILE_DIR)

    hiseq_x_tile_dir.mkdir(parents=True, exist_ok=True)

    # GIVEN an unaligned project directory
    Path(
        flowcell_object.path,
        DemultiplexingDirsAndFiles.UNALIGNED_DIR_NAME,
        f"Project_{flowcell_project_id}",
    ).mkdir(parents=True, exist_ok=True)

    # When post-processing flow cell
    post_demux_api.post_process_flowcell(
        flowcell=flowcell_object,
        flowcell_name=flowcell_object.flowcell_full_name,
        flowcell_path=flowcell_object.path,
    )

    expected_cgstats_select_project_log_file: Path = Path(
        flowcell_object.path,
        "-".join(["stats", str(flowcell_project_id), flowcell_object.flowcell_full_name]) + ".txt",
    )

    expected_cgstats_select_project_log_file.unlink()

    # THEN we should run the command
    assert (
        f"{flowcell_object.flowcell_full_name} copy is complete and delivery will start"
        in caplog.text
    )


def test_finish_flowcell(
    caplog,
    demultiplexed_flowcell_working_directory: Path,
    demultiplex_context: CGConfig,
    flowcell_object: Flowcell,
):
    caplog.set_level(logging.DEBUG)

    # GIVEN a demultiplex context

    # GIVEN a Demultiplexing post process API
    post_demux_api: DemuxPostProcessingHiseqXAPI = DemuxPostProcessingHiseqXAPI(
        config=demultiplex_context
    )

    # GIVEN a not completely copied flow cell
    Path(flowcell_object.path, DemultiplexingDirsAndFiles.Hiseq_X_COPY_COMPLETE).unlink()

    # When post-processing flow cell
    post_demux_api.finish_flowcell(
        bcl_converter=BclConverter.BCL2FASTQ,
        flowcell_name=flowcell_object.flowcell_full_name,
        flowcell_path=flowcell_object.path,
    )

    # Reinstate
    Path(flowcell_object.path, DemultiplexingDirsAndFiles.Hiseq_X_COPY_COMPLETE).touch()

    # THEN we should run the command
    assert f"Check demultiplexed flow cell {flowcell_object.flowcell_full_name}" in caplog.text


def test_finish_all_flowcells(
    caplog,
    demultiplexed_flowcell_working_directory: Path,
    demultiplex_context: CGConfig,
    flowcell_object: Flowcell,
):
    caplog.set_level(logging.DEBUG)

    # GIVEN a demultiplex context

    # GIVEN a Demultiplexing post process API
    post_demux_api: DemuxPostProcessingHiseqXAPI = DemuxPostProcessingHiseqXAPI(
        config=demultiplex_context
    )

    # GIVEN a not completely copied flow cell
    Path(flowcell_object.path, DemultiplexingDirsAndFiles.Hiseq_X_COPY_COMPLETE).unlink()

    # When post-processing flow cell
    post_demux_api.finish_all_flowcells(
        bcl_converter=BclConverter.BCL2FASTQ,
    )

    # Reinstate
    Path(flowcell_object.path, DemultiplexingDirsAndFiles.Hiseq_X_COPY_COMPLETE).touch()

    # THEN we should run the command
    assert f"Check demultiplexed flow cell {flowcell_object.flowcell_full_name}" in caplog.text
