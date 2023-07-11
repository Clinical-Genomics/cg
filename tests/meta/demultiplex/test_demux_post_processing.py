import logging
from pathlib import Path
from typing import Generator, List
from mock import MagicMock, call

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
from cg.store.models import SampleLaneSequencingMetrics


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


def test_add_flow_cell_data_to_housekeeper(demultiplex_context: CGConfig):
    # GIVEN a DemuxPostProcessing API
    demux_post_processing_api = DemuxPostProcessingAPI(demultiplex_context)

    demux_post_processing_api.add_bundle_and_version_if_non_existent = MagicMock()
    demux_post_processing_api.add_tags_if_non_existent = MagicMock()
    demux_post_processing_api.add_sample_sheet_path_to_housekeeper = MagicMock()
    demux_post_processing_api.add_sample_fastq_files_to_housekeeper = MagicMock()

    flow_cell_name: str = "flow_cell_name"
    flow_cell_directory: Path = Path("some/path/to/flow/cell/directory")

    flow_cell = MagicMock()
    flow_cell.path = flow_cell_directory
    flow_cell.id = flow_cell_name

    # WHEN the flow cell data is added to housekeeper
    demux_post_processing_api.store_flow_cell_data_in_housekeeper(flow_cell)

    # THEN the bundle and version is added
    demux_post_processing_api.add_bundle_and_version_if_non_existent.assert_called_once_with(
        bundle_name=flow_cell_name
    )

    # THEN the correct tags are added
    demux_post_processing_api.add_tags_if_non_existent.assert_called_once_with(
        tag_names=[SequencingFileTag.FASTQ, SequencingFileTag.SAMPLE_SHEET, flow_cell_name]
    )

    # THEN the sample sheet is added
    demux_post_processing_api.add_sample_sheet_path_to_housekeeper.assert_called_once_with(
        flow_cell_directory=flow_cell_directory, flow_cell_name=flow_cell_name
    )

    # THEN the fastq files are added
    demux_post_processing_api.add_sample_fastq_files_to_housekeeper.assert_called_once_with(
        flow_cell
    )


def test_add_bundle_and_version_if_non_existent(demultiplex_context: CGConfig):
    # GIVEN a DemuxPostProcessing API
    demux_post_processing_api = DemuxPostProcessingAPI(demultiplex_context)

    demux_post_processing_api.hk_api.bundle = MagicMock(return_value=None)
    demux_post_processing_api.hk_api.create_new_bundle_and_version = MagicMock()

    # WHEN adding a bundle and version which does not exist
    flow_cell_name: str = "flow_cell_name"
    demux_post_processing_api.add_bundle_and_version_if_non_existent(bundle_name=flow_cell_name)

    # THEN that the expected methods were called with the expected arguments
    demux_post_processing_api.hk_api.bundle.assert_called_once_with(name=flow_cell_name)
    demux_post_processing_api.hk_api.create_new_bundle_and_version.assert_called_once_with(
        name=flow_cell_name
    )


def test_add_bundle_and_version_if_already_exists(demultiplex_context: CGConfig):
    # GIVEN a DemuxPostProcessing API
    demux_post_processing_api = DemuxPostProcessingAPI(demultiplex_context)

    mock_bundle = MagicMock()
    demux_post_processing_api.hk_api.bundle = MagicMock(return_value=mock_bundle)
    demux_post_processing_api.hk_api.create_new_bundle_and_version = MagicMock()

    # WHEN adding a bundle and version which already exists
    flow_cell_name: str = "flow_cell_name"
    demux_post_processing_api.add_bundle_and_version_if_non_existent(bundle_name=flow_cell_name)

    # THEN the bundle was retrieved
    demux_post_processing_api.hk_api.bundle.assert_called_once_with(name=flow_cell_name)

    # THEN a new bundle and version was not created
    demux_post_processing_api.hk_api.create_new_bundle_and_version.assert_not_called()


def test_add_tags_if_non_existent(demultiplex_context: CGConfig):
    # GIVEN a DemuxPostProcessing API
    demux_post_processing_api = DemuxPostProcessingAPI(demultiplex_context)

    # GIVEN that the tags do not exist
    demux_post_processing_api.hk_api.get_tag = MagicMock(return_value=None)
    demux_post_processing_api.hk_api.add_tag = MagicMock()

    # WHEN adding new tags
    tag_names = ["tag1", "tag2"]
    demux_post_processing_api.add_tags_if_non_existent(tag_names=tag_names)

    # THEN the expected housekeeper API methods were called to create the tags
    demux_post_processing_api.hk_api.get_tag.assert_has_calls(
        [call(name="tag1"), call(name="tag2")]
    )
    demux_post_processing_api.hk_api.add_tag.assert_has_calls(
        [call(name="tag1"), call(name="tag2")]
    )


def test_add_tags_if_all_exist(demultiplex_context: CGConfig):
    # Given a DemuxPostProcessing API
    demux_post_processing_api = DemuxPostProcessingAPI(demultiplex_context)

    # Mock the methods in the housekeeper API
    demux_post_processing_api.hk_api.get_tag = MagicMock(return_value=MagicMock())
    demux_post_processing_api.hk_api.add_tag = MagicMock()

    # Call the add_tags_if_non_existent method with two tag names
    tag_names = ["tag1", "tag2"]
    demux_post_processing_api.add_tags_if_non_existent(tag_names=tag_names)

    # Assert that the expected methods were called with the expected arguments
    demux_post_processing_api.hk_api.get_tag.assert_has_calls(
        [call(name="tag1"), call(name="tag2")]
    )
    demux_post_processing_api.hk_api.add_tag.assert_not_called()


def test_add_existing_sample_sheet(demultiplex_context: CGConfig, tmpdir_factory):
    # GIVEN a DemuxPostProcessing API
    demux_post_processing_api = DemuxPostProcessingAPI(demultiplex_context)
    demux_post_processing_api.add_file_to_bundle_if_non_existent = MagicMock()

    # GIVEN a flow cell directory and name
    flow_cell_directory: Path = Path(tmpdir_factory.mktemp("flow_cell_directory"))
    sample_sheet_file = Path(flow_cell_directory, DemultiplexingDirsAndFiles.SAMPLE_SHEET_FILE_NAME)
    sample_sheet_file.touch()
    flow_cell_name = "flow_cell_name"

    # WHEN a sample sheet is added
    demux_post_processing_api.add_sample_sheet_path_to_housekeeper(
        flow_cell_directory=flow_cell_directory, flow_cell_name=flow_cell_name
    )

    # THEN add_file_if_non_existent was called with expected arguments
    expected_file_path = Path(
        flow_cell_directory, DemultiplexingDirsAndFiles.SAMPLE_SHEET_FILE_NAME
    )
    expected_tag_names = [SequencingFileTag.SAMPLE_SHEET, flow_cell_name]

    demux_post_processing_api.add_file_to_bundle_if_non_existent.assert_called_once_with(
        file_path=expected_file_path,
        bundle_name=flow_cell_name,
        tag_names=expected_tag_names,
    )


def test_add_fastq_files_without_sample_id(demultiplex_context: CGConfig):
    # GIVEN a DemuxPostProcessing API
    demux_post_processing_api = DemuxPostProcessingAPI(demultiplex_context)

    get_sample_id_from_sample_fastq_path = MagicMock()
    get_sample_id_from_sample_fastq_path.return_value = None

    demux_post_processing_api.add_file_to_bundle_if_non_existent = MagicMock()

    # WHEN add_fastq_files is called
    demux_post_processing_api.add_sample_fastq_files_to_housekeeper(MagicMock())

    # THEN add_file_if_non_existent was not called
    demux_post_processing_api.add_file_to_bundle_if_non_existent.assert_not_called()


def test_add_single_sequencing_metrics_entry_to_statusdb(
    store_with_sequencing_metrics: Store,
    demultiplex_context: CGConfig,
    flow_cell_name: str,
    sample_id: str,
    lane: int = 1,
):
    # GIVEN a DemuxPostProcessing API
    demux_post_processing_api = DemuxPostProcessingAPI(demultiplex_context)

    # GIVEN a sequencing metrics entry
    sequencing_metrics_entry = store_with_sequencing_metrics.get_metrics_entry_by_flow_cell_name_sample_internal_id_and_lane(
        flow_cell_name=flow_cell_name, sample_internal_id=sample_id, lane=lane
    )

    # WHEN adding the sequencing metrics entry to the statusdb
    demux_post_processing_api.add_sequencing_metrics_to_statusdb(
        sample_lane_sequencing_metrics=[sequencing_metrics_entry]
    )

    # THEN the sequencing metrics entry was added to the statusdb
    assert demux_post_processing_api.status_db.get_metrics_entry_by_flow_cell_name_sample_internal_id_and_lane(
        flow_cell_name=flow_cell_name, sample_internal_id=sample_id, lane=lane
    )


def test_update_sample_read_count(demultiplex_context: CGConfig):
    # GIVEN a DemuxPostProcessing API
    demux_post_processing_api = DemuxPostProcessingAPI(demultiplex_context)

    # GIVEN a sample id and a q30 threshold
    sample_id = "sample_1"
    q30_threshold = 0

    # GIVEN a sample and a read count
    sample = MagicMock()
    read_count = 100

    # GIVEN a mocked status_db
    status_db = MagicMock()
    status_db.get_sample_by_internal_id.return_value = sample
    status_db.get_number_of_reads_for_sample_passing_q30_threshold.return_value = read_count
    demux_post_processing_api.status_db = status_db

    # WHEN calling update_sample_read_count
    demux_post_processing_api.update_sample_read_count(sample_id, q30_threshold)

    # THEN get_sample_by_internal_id is called with the correct argument
    status_db.get_sample_by_internal_id.assert_called_with(sample_id)

    # THEN get_number_of_reads_for_sample_passing_q30_threshold is called with the correct arguments
    status_db.get_number_of_reads_for_sample_passing_q30_threshold.assert_called_with(
        sample_internal_id=sample_id,
        q30_threshold=q30_threshold,
    )

    # THEN the calculated_read_count has been updated with the read count for the sample
    assert sample.calculated_read_count == read_count


def test_post_processing_of_flow_cell_demultiplexed_with_bclconvert(
    demultiplex_context: CGConfig,
    flow_cell_directory_name_demultiplexed_with_bcl_convert: str,
    flow_cell_name_demultiplexed_with_bcl_convert: str,
    demultiplexed_flow_cells_directory: Path,
    bcl_convert_demultiplexed_flow_cell_sample_ids: List[str],
):
    # GIVEN a DemuxPostProcessing API
    demux_post_processing_api = DemuxPostProcessingAPI(demultiplex_context)

    # GIVEN a directory with a flow cell demultiplexed with BCL Convert
    demux_post_processing_api.demux_api.out_dir = demultiplexed_flow_cells_directory

    # WHEN post processing the demultiplexed flow cell
    demux_post_processing_api.finish_flow_cell_temp(
        flow_cell_directory_name_demultiplexed_with_bcl_convert
    )

    # THEN a flow cell was created in statusdb
    assert demux_post_processing_api.status_db.get_flow_cell_by_name(
        flow_cell_name_demultiplexed_with_bcl_convert
    )

    # THEN sequencing metrics were created for the flow cell
    assert (
        demux_post_processing_api.status_db._get_query(table=SampleLaneSequencingMetrics)
        .filter(
            SampleLaneSequencingMetrics.flow_cell_name
            == flow_cell_name_demultiplexed_with_bcl_convert
        )
        .all()
    )

    # THEN the read count was calculated for all samples in the flow cell directory
    for sample_id in bcl_convert_demultiplexed_flow_cell_sample_ids:
        sample = demux_post_processing_api.status_db.get_sample_by_internal_id(sample_id)
        assert sample is not None
        assert sample.calculated_read_count

    # THEN a bundle was added to Housekeeper for the flow cell
    assert demux_post_processing_api.hk_api.bundle(flow_cell_name_demultiplexed_with_bcl_convert)

    # THEN a bundle was added to Housekeeper for each sample
    for sample_id in bcl_convert_demultiplexed_flow_cell_sample_ids:
        assert demux_post_processing_api.hk_api.bundle(sample_id)

    # THEN a sample sheet was added to Housekeeper
    assert demux_post_processing_api.hk_api.get_files(
        tags=[SequencingFileTag.SAMPLE_SHEET],
        bundle=flow_cell_name_demultiplexed_with_bcl_convert,
    ).all()

    # THEN sample fastq files were added to Housekeeper tagged with FASTQ and the flow cell name
    for sample_id in bcl_convert_demultiplexed_flow_cell_sample_ids:
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
    demultiplexed_flow_cells_directory: Path,
    bcl2fastq_demultiplexed_flow_cell_sample_ids: List[str],
):
    # GIVEN a DemuxPostProcessing API
    demux_post_processing_api = DemuxPostProcessingAPI(demultiplex_context)

    # GIVEN a directory with a flow cell demultiplexed with bcl2fastq
    demux_post_processing_api.demux_api.out_dir = demultiplexed_flow_cells_directory

    # WHEN post processing the demultiplexed flow cell
    demux_post_processing_api.finish_flow_cell_temp(
        flow_cell_directory_name_demultiplexed_with_bcl2fastq
    )

    # THEN a flow cell was created in statusdb
    assert demux_post_processing_api.status_db.get_flow_cell_by_name(
        flow_cell_name_demultiplexed_with_bcl2fastq
    )

    # THEN sequencing metrics were created for the flow cell
    assert (
        demux_post_processing_api.status_db._get_query(table=SampleLaneSequencingMetrics)
        .filter(
            SampleLaneSequencingMetrics.flow_cell_name
            == flow_cell_name_demultiplexed_with_bcl2fastq
        )
        .all()
    )

    # THEN the read count was calculated for all samples in the flow cell directory
    for sample_id in bcl2fastq_demultiplexed_flow_cell_sample_ids:
        sample = demux_post_processing_api.status_db.get_sample_by_internal_id(sample_id)
        assert sample is not None
        assert sample.calculated_read_count

    # THEN a bundle was added to Housekeeper for the flow cell
    assert demux_post_processing_api.hk_api.bundle(flow_cell_name_demultiplexed_with_bcl2fastq)

    # THEN a bundle was added to Housekeeper for each sample
    for sample_id in bcl2fastq_demultiplexed_flow_cell_sample_ids:
        assert demux_post_processing_api.hk_api.bundle(sample_id)

    # THEN a sample sheet was added to Housekeeper
    assert demux_post_processing_api.hk_api.get_files(
        tags=[SequencingFileTag.SAMPLE_SHEET],
        bundle=flow_cell_name_demultiplexed_with_bcl2fastq,
    ).all()

    # THEN sample fastq files were added to Housekeeper tagged with FASTQ and the flow cell name
    for sample_id in bcl2fastq_demultiplexed_flow_cell_sample_ids:
        assert demux_post_processing_api.hk_api.get_files(
            tags=[SequencingFileTag.FASTQ, flow_cell_name_demultiplexed_with_bcl2fastq],
            bundle=sample_id,
        ).all()

    # THEN a delivery file was created in the flow cell directory
    delivery_path = Path(
        demux_post_processing_api.demux_api.out_dir,
        flow_cell_directory_name_demultiplexed_with_bcl2fastq,
        DemultiplexingDirsAndFiles.DELIVERY,
    )

    assert delivery_path.exists()
