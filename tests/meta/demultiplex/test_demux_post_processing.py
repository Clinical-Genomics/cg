import logging
from pathlib import Path

from cg.constants.demultiplexing import DemultiplexingDirsAndFiles, BclConverter
from cg.meta.demultiplex.demux_post_processing import (
    DemuxPostProcessingAPI,
    DemuxPostProcessingHiseqXAPI,
)
from cg.meta.transfer import TransferFlowcell
from cg.models.cg_config import CGConfig
from cg.models.demultiplex.flowcell import Flowcell
from cg.store import Store


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
    flow_cell_project_id: int,
    cgstats_select_project_log_file: Path,
):
    caplog.set_level(logging.INFO)

    # GIVEN a demultiplex context

    # GIVEN a Demultiplexing post process API
    post_demux_api: DemuxPostProcessingHiseqXAPI = DemuxPostProcessingHiseqXAPI(
        config=demultiplex_context
    )

    # GIVEN an unaligned project directory
    Path(flowcell_object.path, "Unaligned", f"Project_{flow_cell_project_id}").mkdir(
        parents=True, exist_ok=True
    )

    # When processing project with cgstats
    post_demux_api.cgstats_select_project(
        flowcell_name=flowcell_object.flowcell_full_name, flowcell_path=flowcell_object.path
    )

    # THEN we should have created a stats outfile
    assert cgstats_select_project_log_file.exists()

    # Clean up from calling cgstats_select_project
    cgstats_select_project_log_file.unlink()

    # THEN we should run the command
    assert f"select --project {flow_cell_project_id}" in caplog.text


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

    # When processing lane stats with cgstats
    post_demux_api.cgstats_lanestats(flowcell_path=flowcell_object.path)

    # THEN we should run the command
    assert f"lanestats {flowcell_object.path}" in caplog.text


def test_post_process_flowcell_copy_not_completed(
    caplog,
    demultiplexed_flowcell_working_directory: Path,
    demultiplex_context: CGConfig,
    flowcell_object: Flowcell,
    hiseq_x_copy_complete_file: Path,
):
    caplog.set_level(logging.DEBUG)

    # GIVEN a demultiplex context

    # GIVEN a Demultiplexing post process API
    post_demux_api: DemuxPostProcessingHiseqXAPI = DemuxPostProcessingHiseqXAPI(
        config=demultiplex_context
    )

    # GIVEN a not completely copied flow cell
    if hiseq_x_copy_complete_file.exists():
        hiseq_x_copy_complete_file.unlink()

    # When post-processing flow cell
    post_demux_api.post_process_flowcell(
        flowcell=flowcell_object,
        flowcell_name=flowcell_object.flowcell_full_name,
        flowcell_path=flowcell_object.path,
    )

    # Reinstate
    hiseq_x_copy_complete_file.touch()

    # THEN we should log that copy is not complete
    assert f"{flowcell_object.flowcell_full_name} is not yet completely copied" in caplog.text


def test_post_process_flowcell_delivery_started(
    caplog,
    demultiplexed_flowcell_working_directory: Path,
    demultiplexing_delivery_file: Path,
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
    demultiplexing_delivery_file.touch()

    # When post-processing flow cell
    post_demux_api.post_process_flowcell(
        flowcell=flowcell_object,
        flowcell_name=flowcell_object.flowcell_full_name,
        flowcell_path=flowcell_object.path,
    )

    # Clean up
    demultiplexing_delivery_file.unlink()

    # THEN we should log that the delivery has already started
    assert (
        f"{flowcell_object.flowcell_full_name} copy is complete and delivery has already started"
        in caplog.text
    )


def test_post_process_flowcell_not_hiseq_x(
    caplog,
    demultiplexed_flowcell_working_directory: Path,
    demultiplex_context: CGConfig,
    flowcell_object: Flowcell,
    hiseq_x_tile_dir: Path,
):
    caplog.set_level(logging.DEBUG)

    # GIVEN a demultiplex context

    # GIVEN a Demultiplexing post process API
    post_demux_api: DemuxPostProcessingHiseqXAPI = DemuxPostProcessingHiseqXAPI(
        config=demultiplex_context
    )

    # GIVEN no hiseq X flow cell
    if hiseq_x_tile_dir.exists():
        hiseq_x_tile_dir.rmdir()

    # When post-processing flow cell
    post_demux_api.post_process_flowcell(
        flowcell=flowcell_object,
        flowcell_name=flowcell_object.flowcell_full_name,
        flowcell_path=flowcell_object.path,
    )

    # THEN we should log that this is not an Hiseq X flow cell
    assert f"{flowcell_object.flowcell_full_name} is not an Hiseq X flow cell" in caplog.text


def test_post_process_flowcell(
    caplog,
    cgstats_select_project_log_file: Path,
    demultiplexed_flowcell_working_directory: Path,
    demultiplexing_delivery_file: Path,
    demultiplex_context: CGConfig,
    flowcell_object: Flowcell,
    flow_cell_project_id: int,
    flowcell_store: Store,
    hiseq_x_tile_dir: Path,
    transfer_flowcell_api,
    mocker,
    tmp_file,
):
    caplog.set_level(logging.DEBUG)

    # GIVEN a demultiplex context

    # GIVEN a Demultiplexing post process API
    post_demux_api: DemuxPostProcessingHiseqXAPI = DemuxPostProcessingHiseqXAPI(
        config=demultiplex_context
    )

    # GIVEN a Hiseq X tile directory
    hiseq_x_tile_dir.mkdir(parents=True, exist_ok=True)

    # GIVEN an unaligned project directory
    Path(
        flowcell_object.path,
        DemultiplexingDirsAndFiles.UNALIGNED_DIR_NAME,
        f"Project_{flow_cell_project_id}",
    ).mkdir(parents=True, exist_ok=True)

    mocker.patch.object(TransferFlowcell, "_sample_sheet_path")
    TransferFlowcell._sample_sheet_path.return_value = tmp_file.as_posix()

    # When post-processing flow cell
    post_demux_api.post_process_flowcell(
        flowcell=flowcell_object,
        flowcell_name=flowcell_object.flowcell_full_name,
        flowcell_path=flowcell_object.path,
    )

    # THEN a delivery file should have been created
    assert demultiplexing_delivery_file.exists()

    # Clean up
    cgstats_select_project_log_file.unlink()
    demultiplexing_delivery_file.unlink()

    # THEN we should log that post-processing will begin
    assert (
        f"{flowcell_object.flowcell_full_name} copy is complete and delivery will start"
        in caplog.text
    )

    # THEN we should also transfer the flow cell
    assert f"Flowcell added: {flowcell_object.flowcell_full_name}" in caplog.text


def test_finish_flowcell(
    caplog,
    demultiplexed_flowcell_working_directory: Path,
    demultiplex_context: CGConfig,
    flowcell_object: Flowcell,
    hiseq_x_copy_complete_file: Path,
):
    caplog.set_level(logging.DEBUG)

    # GIVEN a demultiplex context

    # GIVEN a Demultiplexing post process API
    post_demux_api: DemuxPostProcessingHiseqXAPI = DemuxPostProcessingHiseqXAPI(
        config=demultiplex_context
    )

    # GIVEN a not completely copied flow cell
    hiseq_x_copy_complete_file.unlink()

    # When post-processing flow cell
    post_demux_api.finish_flowcell(
        bcl_converter=BclConverter.BCL2FASTQ,
        flowcell_name=flowcell_object.flowcell_full_name,
        flowcell_path=flowcell_object.path,
    )

    # Reinstate
    hiseq_x_copy_complete_file.touch()

    # THEN we should log that we are checking flow cell
    assert f"Check demultiplexed flow cell {flowcell_object.flowcell_full_name}" in caplog.text


def test_finish_all_flowcells(
    caplog,
    demultiplexed_flowcell_working_directory: Path,
    demultiplex_context: CGConfig,
    flowcell_object: Flowcell,
    hiseq_x_copy_complete_file: Path,
):
    caplog.set_level(logging.DEBUG)

    # GIVEN a demultiplex context

    # GIVEN a Demultiplexing post process API
    post_demux_api: DemuxPostProcessingHiseqXAPI = DemuxPostProcessingHiseqXAPI(
        config=demultiplex_context
    )

    # GIVEN a not completely copied flow cell
    hiseq_x_copy_complete_file.unlink()

    # When post-processing flow cell
    post_demux_api.finish_all_flowcells(
        bcl_converter=BclConverter.BCL2FASTQ,
    )

    # Reinstate
    hiseq_x_copy_complete_file.touch()

    # THEN we should log that we are checking flow cell
    assert f"Check demultiplexed flow cell {flowcell_object.flowcell_full_name}" in caplog.text
