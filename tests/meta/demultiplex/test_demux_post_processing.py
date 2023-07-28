import logging
from pathlib import Path
from typing import Generator, List


from cg.constants.demultiplexing import BclConverter, DemultiplexingDirsAndFiles
from cg.constants.housekeeper_tags import SequencingFileTag
from cg.meta.demultiplex.demux_post_processing import (
    DemuxPostProcessingAPI,
    DemuxPostProcessingHiseqXAPI,
)
from cg.meta.transfer import TransferFlowCell
from cg.models.cg_config import CGConfig
from cg.models.demultiplex.demux_results import DemuxResults
from cg.models.demultiplex.flow_cell import FlowCellDirectoryData
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


def test_add_to_cgstats_dry_run(
    caplog,
    demultiplex_context: CGConfig,
    bcl2fastq_flow_cell: FlowCellDirectoryData,
):
    caplog.set_level(logging.INFO)

    # GIVEN a demultiplex context

    # GIVEN a Demultiplexing post process API
    post_demux_api: DemuxPostProcessingHiseqXAPI = DemuxPostProcessingHiseqXAPI(
        config=demultiplex_context
    )

    # GIVEN dry run set to True
    post_demux_api.set_dry_run(dry_run=True)

    # When adding to cgstats
    post_demux_api.add_to_cgstats(flow_cell_path=bcl2fastq_flow_cell.path)

    # THEN we should just log and exit
    assert "Dry run will not add flow cell stats" in caplog.text


def test_add_to_cgstats(
    caplog,
    demultiplex_context: CGConfig,
    bcl2fastq_flow_cell: FlowCellDirectoryData,
):
    caplog.set_level(logging.INFO)

    # GIVEN a demultiplex context

    # GIVEN a Demultiplexing post process API
    post_demux_api: DemuxPostProcessingHiseqXAPI = DemuxPostProcessingHiseqXAPI(
        config=demultiplex_context
    )

    # When adding to cgstats
    post_demux_api.add_to_cgstats(flow_cell_path=bcl2fastq_flow_cell.path)

    # THEN we should run the command
    assert f"add --machine X -u Unaligned {bcl2fastq_flow_cell.path}" in caplog.text


def test_cgstats_select_project_dry_run(
    caplog,
    demultiplex_context: CGConfig,
    bcl2fastq_flow_cell: FlowCellDirectoryData,
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
    Path(bcl2fastq_flow_cell.path, "Unaligned", f"Project_{flow_cell_project_id}").mkdir(
        parents=True, exist_ok=True
    )

    # GIVEN dry run set to True
    post_demux_api.set_dry_run(dry_run=True)

    # When processing project with cgstats
    post_demux_api.cgstats_select_project(
        flow_cell_id=bcl2fastq_flow_cell.id, flow_cell_path=bcl2fastq_flow_cell.path
    )

    # THEN we should just log and exit
    assert "Dry run will not process selected project" in caplog.text


def test_cgstats_select_project(
    caplog,
    demultiplex_context: CGConfig,
    bcl2fastq_flow_cell: FlowCellDirectoryData,
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
    Path(bcl2fastq_flow_cell.path, "Unaligned", f"Project_{flow_cell_project_id}").mkdir(
        parents=True, exist_ok=True
    )

    # When processing project with cgstats
    post_demux_api.cgstats_select_project(
        flow_cell_id=bcl2fastq_flow_cell.id, flow_cell_path=bcl2fastq_flow_cell.path
    )

    # THEN we should have created a stats outfile
    assert cgstats_select_project_log_file.exists()

    # Clean up from calling cgstats_select_project
    cgstats_select_project_log_file.unlink()

    # THEN we should run the command
    assert f"select --project {flow_cell_project_id} {bcl2fastq_flow_cell.id}" in caplog.text


def test_cgstats_lanestats_dry_run(
    caplog,
    demultiplex_context: CGConfig,
    bcl2fastq_flow_cell: FlowCellDirectoryData,
):
    caplog.set_level(logging.INFO)

    # GIVEN a demultiplex context

    # GIVEN a Demultiplexing post process API
    post_demux_api: DemuxPostProcessingHiseqXAPI = DemuxPostProcessingHiseqXAPI(
        config=demultiplex_context
    )

    # GIVEN dry run set to True
    post_demux_api.set_dry_run(dry_run=True)

    # When processing lane stats with cgstats
    post_demux_api.cgstats_lanestats(flow_cell_path=bcl2fastq_flow_cell.path)

    # THEN we should run the command
    assert "Dry run will not add lane stats" in caplog.text


def test_cgstats_lanestats(
    caplog,
    demultiplex_context: CGConfig,
    bcl2fastq_flow_cell: FlowCellDirectoryData,
):
    caplog.set_level(logging.INFO)

    # GIVEN a demultiplex context

    # GIVEN a Demultiplexing post process API
    post_demux_api: DemuxPostProcessingHiseqXAPI = DemuxPostProcessingHiseqXAPI(
        config=demultiplex_context
    )

    # When processing lane stats with cgstats
    post_demux_api.cgstats_lanestats(flow_cell_path=bcl2fastq_flow_cell.path)

    # THEN we should run the command
    assert f"lanestats {bcl2fastq_flow_cell.path}" in caplog.text


def test_finish_flow_cell_copy_not_completed(
    caplog,
    demultiplex_context: CGConfig,
    bcl2fastq_flow_cell: FlowCellDirectoryData,
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

    # WHEN finishing flow cell
    post_demux_api.finish_flow_cell(
        bcl_converter=BclConverter.BCL2FASTQ,
        flow_cell_name=bcl2fastq_flow_cell.full_name,
        flow_cell_path=bcl2fastq_flow_cell.path,
    )

    # Reinstate
    hiseq_x_copy_complete_file.touch()

    # THEN we should log that copy is not complete
    assert f"{bcl2fastq_flow_cell.full_name} is not yet completely copied" in caplog.text


def test_finish_flow_cell_delivery_started(
    caplog,
    demultiplexing_delivery_file: Path,
    demultiplex_context: CGConfig,
    bcl2fastq_flow_cell: FlowCellDirectoryData,
):
    caplog.set_level(logging.DEBUG)

    # GIVEN a demultiplex context

    # GIVEN a Demultiplexing post process API
    post_demux_api: DemuxPostProcessingHiseqXAPI = DemuxPostProcessingHiseqXAPI(
        config=demultiplex_context
    )

    # GIVEN an already started flag file
    demultiplexing_delivery_file.touch()

    # WHEN finishing flow cell
    post_demux_api.finish_flow_cell(
        bcl_converter=BclConverter.BCL2FASTQ,
        flow_cell_name=bcl2fastq_flow_cell.full_name,
        flow_cell_path=bcl2fastq_flow_cell.path,
    )

    # Clean up
    demultiplexing_delivery_file.unlink()

    # THEN we should log that the delivery has already started
    assert (
        f"{bcl2fastq_flow_cell.full_name} copy is complete and delivery has already started"
        in caplog.text
    )


def test_finish_flow_cell_delivery_not_hiseq_x(
    caplog,
    demultiplex_context: CGConfig,
    bcl2fastq_flow_cell: FlowCellDirectoryData,
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

    # WHEN finishing flow cell
    post_demux_api.finish_flow_cell(
        bcl_converter=BclConverter.BCL2FASTQ,
        flow_cell_name=bcl2fastq_flow_cell.full_name,
        flow_cell_path=bcl2fastq_flow_cell.path,
    )

    # THEN we should log that this is not an Hiseq X flow cell
    assert f"{bcl2fastq_flow_cell.full_name} is not an Hiseq X flow cell" in caplog.text


def test_finish_flow_cell_ready(
    caplog,
    demultiplex_context: CGConfig,
    bcl2fastq_flow_cell: FlowCellDirectoryData,
    flow_cell_project_id: int,
    demultiplexing_delivery_file: Path,
    hiseq_x_tile_dir: Path,
    transfer_flow_cell_api: Generator[TransferFlowCell, None, None],
):
    caplog.set_level(logging.INFO)

    # GIVEN a demultiplex context

    # GIVEN a Demultiplexing post process API
    post_demux_api: DemuxPostProcessingHiseqXAPI = DemuxPostProcessingHiseqXAPI(
        config=demultiplex_context
    )

    # GIVEN dry run set to True
    post_demux_api.set_dry_run(dry_run=True)

    # GIVEN a Hiseq X tile directory
    hiseq_x_tile_dir.mkdir(parents=True, exist_ok=True)

    # GIVEN an unaligned project directory
    Path(
        bcl2fastq_flow_cell.path,
        DemultiplexingDirsAndFiles.UNALIGNED_DIR_NAME,
        f"Project_{flow_cell_project_id}",
    ).mkdir(parents=True, exist_ok=True)

    # WHEN finishing flow cell
    post_demux_api.finish_flow_cell(
        bcl_converter=BclConverter.BCL2FASTQ,
        flow_cell_name=bcl2fastq_flow_cell.full_name,
        flow_cell_path=bcl2fastq_flow_cell.path,
    )

    # THEN we should log that post-processing will begin
    assert (
        f"{bcl2fastq_flow_cell.full_name} copy is complete and delivery will start" in caplog.text
    )


def test_post_process_flow_cell_dry_run(
    bcl2fastq_demux_results: DemuxResults,
    caplog,
    demultiplexing_delivery_file: Path,
    demultiplex_context: CGConfig,
    bcl2fastq_flow_cell: FlowCellDirectoryData,
    flow_cell_project_id: int,
    flowcell_store: Store,
    hiseq_x_tile_dir: Path,
    transfer_flow_cell_api: Generator[TransferFlowCell, None, None],
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
        bcl2fastq_flow_cell.path,
        DemultiplexingDirsAndFiles.UNALIGNED_DIR_NAME,
        f"Project_{flow_cell_project_id}",
    ).mkdir(parents=True, exist_ok=True)

    # GIVEN dry run set to True
    post_demux_api.set_dry_run(dry_run=True)

    # WHEN post-processing flow cell
    post_demux_api.post_process_flow_cell(demux_results=bcl2fastq_demux_results)

    # THEN a delivery file should not have been created
    assert not demultiplexing_delivery_file.exists()

    # THEN we should log that we will not commit
    assert "Dry run will not commit flow cell to database" in caplog.text


def test_post_process_flow_cell(
    bcl2fastq_demux_results: DemuxResults,
    caplog,
    cgstats_select_project_log_file: Path,
    demultiplexing_delivery_file: Path,
    demultiplex_context: CGConfig,
    bcl2fastq_flow_cell: FlowCellDirectoryData,
    flow_cell_project_id: int,
    hiseq_x_tile_dir: Path,
    transfer_flow_cell_api: Generator[TransferFlowCell, None, None],
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
        bcl2fastq_flow_cell.path,
        DemultiplexingDirsAndFiles.UNALIGNED_DIR_NAME,
        f"Project_{flow_cell_project_id}",
    ).mkdir(parents=True, exist_ok=True)

    # WHEN post-processing flow cell
    post_demux_api.post_process_flow_cell(demux_results=bcl2fastq_demux_results)

    # THEN a delivery file should have been created
    assert demultiplexing_delivery_file.exists()

    # Clean up
    cgstats_select_project_log_file.unlink()
    demultiplexing_delivery_file.unlink()

    # THEN we should also transfer the flow cell
    assert f"Flow cell added: {bcl2fastq_flow_cell.id}" in caplog.text


def test_finish_flow_cell(
    caplog,
    demultiplex_context: CGConfig,
    bcl2fastq_flow_cell: FlowCellDirectoryData,
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
    post_demux_api.finish_flow_cell(
        bcl_converter=BclConverter.BCL2FASTQ,
        flow_cell_name=bcl2fastq_flow_cell.full_name,
        flow_cell_path=bcl2fastq_flow_cell.path,
    )

    # Reinstate
    hiseq_x_copy_complete_file.touch()

    # THEN we should log that we are checking flow cell
    assert f"Check demultiplexed flow cell {bcl2fastq_flow_cell.full_name}" in caplog.text


def test_finish_all_flowcells(
    caplog,
    demultiplexed_flow_cell_working_directory: Path,
    demultiplex_context: CGConfig,
    bcl2fastq_flow_cell: FlowCellDirectoryData,
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
    post_demux_api.finish_all_flow_cells(
        bcl_converter=BclConverter.BCL2FASTQ,
    )

    # Reinstate
    hiseq_x_copy_complete_file.touch()

    # THEN we should log that we are checking flow cell
    assert f"Check demultiplexed flow cell {bcl2fastq_flow_cell.full_name}" in caplog.text


def test_post_processing_of_flow_cell_demultiplexed_with_bclconvert(
    demultiplex_context: CGConfig,
    flow_cell_directory_name_demultiplexed_with_bcl_convert: str,
    flow_cell_name_demultiplexed_with_bcl_convert: str,
    demultiplexed_flow_cells_tmp_directory: Path,
    bcl_convert_demultiplexed_flow_cell_sample_internal_ids: List[str],
    novaseq_6000_dir: Path,
):
    # GIVEN a DemuxPostProcessing API
    demux_post_processing_api = DemuxPostProcessingAPI(demultiplex_context)

    # GIVEN a directory with a flow cell demultiplexed with BCL Convert
    demux_post_processing_api.demux_api.out_dir = demultiplexed_flow_cells_tmp_directory
    demux_post_processing_api.demux_api.run_dir = novaseq_6000_dir

    # WHEN post processing the demultiplexed flow cell
    demux_post_processing_api.finish_flow_cell_temp(
        flow_cell_directory_name_demultiplexed_with_bcl_convert
    )

    # THEN a flow cell was created in statusdb
    assert demux_post_processing_api.status_db.get_flow_cell_by_name(
        flow_cell_name_demultiplexed_with_bcl_convert
    )

    # THEN sequencing metrics were created for the flow cell
    assert demux_post_processing_api.status_db.get_sample_lane_sequencing_metrics_by_flow_cell_name(
        flow_cell_name=flow_cell_name_demultiplexed_with_bcl_convert
    )
    # THEN the read count was calculated for all samples in the flow cell directory
    for sample_id in bcl_convert_demultiplexed_flow_cell_sample_internal_ids:
        sample = demux_post_processing_api.status_db.get_sample_by_internal_id(sample_id)
        assert sample is not None
        assert sample.calculated_read_count

    # THEN a bundle was added to Housekeeper for the flow cell
    assert demux_post_processing_api.hk_api.bundle(flow_cell_name_demultiplexed_with_bcl_convert)

    # THEN a bundle was added to Housekeeper for each sample
    for sample_id in bcl_convert_demultiplexed_flow_cell_sample_internal_ids:
        assert demux_post_processing_api.hk_api.bundle(sample_id)

    # THEN a sample sheet was added to Housekeeper
    assert demux_post_processing_api.hk_api.get_files(
        tags=[SequencingFileTag.SAMPLE_SHEET],
        bundle=flow_cell_name_demultiplexed_with_bcl_convert,
    ).all()

    # THEN sample fastq files were added to Housekeeper tagged with FASTQ and the flow cell name
    for sample_id in bcl_convert_demultiplexed_flow_cell_sample_internal_ids:
        assert demux_post_processing_api.hk_api.get_files(
            tags=[SequencingFileTag.FASTQ, flow_cell_name_demultiplexed_with_bcl_convert],
            bundle=sample_id,
        ).all()

    # THEN a delivery file was created in the flow cell directory
    delivery_path = Path(
        demux_post_processing_api.demux_api.out_dir,
        flow_cell_directory_name_demultiplexed_with_bcl_convert,
        DemultiplexingDirsAndFiles.DELIVERY,
    )

    assert delivery_path.exists()


def test_post_processing_of_flow_cell_demultiplexed_with_bcl2fastq(
    demultiplex_context: CGConfig,
    flow_cell_directory_name_demultiplexed_with_bcl2fastq: str,
    flow_cell_name_demultiplexed_with_bcl2fastq: str,
    demultiplexed_flow_cells_tmp_directory: Path,
    hiseq_dir: Path,
    bcl2fastq_demultiplexed_flow_cell_sample_internal_ids: List[str],
):
    # GIVEN a DemuxPostProcessing API
    demux_post_processing_api = DemuxPostProcessingAPI(demultiplex_context)

    # GIVEN a directory with a flow cell demultiplexed with bcl2fastq
    demux_post_processing_api.demux_api.out_dir = demultiplexed_flow_cells_tmp_directory
    demux_post_processing_api.demux_api.run_dir = hiseq_dir

    # WHEN post processing the demultiplexed flow cell
    demux_post_processing_api.finish_flow_cell_temp(
        flow_cell_directory_name_demultiplexed_with_bcl2fastq
    )

    # THEN a flow cell was created in statusdb
    assert demux_post_processing_api.status_db.get_flow_cell_by_name(
        flow_cell_name_demultiplexed_with_bcl2fastq
    )

    # THEN sequencing metrics were created for the flow cell
    assert demux_post_processing_api.status_db.get_sample_lane_sequencing_metrics_by_flow_cell_name(
        flow_cell_name=flow_cell_name_demultiplexed_with_bcl2fastq
    )

    # THEN the read count was calculated for all samples in the flow cell directory
    for sample_internal_id in bcl2fastq_demultiplexed_flow_cell_sample_internal_ids:
        sample = demux_post_processing_api.status_db.get_sample_by_internal_id(sample_internal_id)
        assert sample is not None
        assert sample.calculated_read_count

    # THEN a bundle was added to Housekeeper for the flow cell
    assert demux_post_processing_api.hk_api.bundle(flow_cell_name_demultiplexed_with_bcl2fastq)

    # THEN a bundle was added to Housekeeper for each sample
    for sample_internal_id in bcl2fastq_demultiplexed_flow_cell_sample_internal_ids:
        assert demux_post_processing_api.hk_api.bundle(sample_internal_id)

    # THEN a sample sheet was added to Housekeeper
    assert demux_post_processing_api.hk_api.get_files(
        tags=[SequencingFileTag.SAMPLE_SHEET],
        bundle=flow_cell_name_demultiplexed_with_bcl2fastq,
    ).all()

    # THEN sample fastq files were added to Housekeeper tagged with FASTQ and the flow cell name
    for sample_internal_id in bcl2fastq_demultiplexed_flow_cell_sample_internal_ids:
        assert demux_post_processing_api.hk_api.get_files(
            tags=[SequencingFileTag.FASTQ, flow_cell_name_demultiplexed_with_bcl2fastq],
            bundle=sample_internal_id,
        ).all()

    # THEN a delivery file was created in the flow cell directory
    delivery_path = Path(
        demux_post_processing_api.demux_api.out_dir,
        flow_cell_directory_name_demultiplexed_with_bcl2fastq,
        DemultiplexingDirsAndFiles.DELIVERY,
    )

    assert delivery_path.exists()
