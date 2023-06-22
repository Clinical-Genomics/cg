from datetime import datetime
import logging
from pathlib import Path
from typing import Generator

from mock import MagicMock, call

from cg.constants.demultiplexing import DemultiplexingDirsAndFiles, BclConverter
from cg.constants.housekeeper_tags import SequencingFileTag
from cg.meta.demultiplex import demux_post_processing
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


def test_is_bcl2fastq_folder_structure(
    demultiplex_context: CGConfig, bcl2fastq_folder_structure: Path
):
    """Test is_bcl2fastq_demux_folder_structure with a folder structure that follows the bcl2fastq folder structure."""
    # GIVEN a bcl2fastq folder structure
    demux_post_processing_api = DemuxPostProcessingAPI(demultiplex_context)
    demux_post_processing_api.demux_api.out_dir = bcl2fastq_folder_structure

    # WHEN checking if it is a bcl2fastq folder structure
    is_bcl2fastq_folder_structure = demux_post_processing_api.is_bcl2fastq_demux_folder_structure(
        flow_cell_directory=bcl2fastq_folder_structure
    )

    # THEN it should be a bcl2fastq folder structure
    assert is_bcl2fastq_folder_structure is True


def test_is_not_bcl2fastq_folder_structure(
    demultiplex_context: CGConfig, not_bcl2fastq_folder_structure: Path
):
    """Test is_bcl2fastq_demux_folder_structure with a folder structure that does not follow the bcl2fastq output."""

    # GIVEN not a bcl2fastq folder structure
    demux_post_processing_api = DemuxPostProcessingAPI(demultiplex_context)
    demux_post_processing_api.flow_cell_dir = not_bcl2fastq_folder_structure

    # WHEN checking if it is a bcl2fastq folder structure
    is_bcl2fastq_folder_structure = demux_post_processing_api.is_bcl2fastq_demux_folder_structure(
        flow_cell_directory=not_bcl2fastq_folder_structure
    )

    # THEN it should not be a bcl2fastq folder structure
    assert is_bcl2fastq_folder_structure is False


def test_add_flow_cell_data_to_housekeeper(demultiplex_context: CGConfig):
    # GIVEN a DemuxPostProcessing API
    demux_post_processing_api = DemuxPostProcessingAPI(demultiplex_context)

    demux_post_processing_api.add_bundle_and_version_if_non_existent = MagicMock()
    demux_post_processing_api.add_tags_if_non_existent = MagicMock()
    demux_post_processing_api.add_sample_sheet = MagicMock()
    demux_post_processing_api.add_sample_fastq_files = MagicMock()

    flow_cell_name: str = "flow_cell_name"
    flow_cell_directory: Path = Path("some/path/to/flow/cell/directory")

    # WHEN the flow cell data is added to housekeeper
    demux_post_processing_api.add_flow_cell_data_to_housekeeper(
        flow_cell_directory=flow_cell_directory, flow_cell_name=flow_cell_name
    )

    # THEN the bundle and version is added
    demux_post_processing_api.add_bundle_and_version_if_non_existent.assert_called_once_with(
        flow_cell_name=flow_cell_name
    )

    # THEN the correct tags are added
    demux_post_processing_api.add_tags_if_non_existent.assert_called_once_with(
        tag_names=[SequencingFileTag.FASTQ, SequencingFileTag.SAMPLE_SHEET, flow_cell_name]
    )

    # THEN the sample sheet is added
    demux_post_processing_api.add_sample_sheet.assert_called_once_with(
        flow_cell_directory=flow_cell_directory, flow_cell_name=flow_cell_name
    )

    # THEN the fastq files are added
    demux_post_processing_api.add_sample_fastq_files.assert_called_once_with(
        flow_cell_directory=flow_cell_directory, flow_cell_name=flow_cell_name
    )


def test_add_bundle_and_version_if_non_existent(demultiplex_context: CGConfig):
    # GIVEN a DemuxPostProcessing API
    demux_post_processing_api = DemuxPostProcessingAPI(demultiplex_context)

    demux_post_processing_api.hk_api.bundle = MagicMock(return_value=None)
    demux_post_processing_api.hk_api.create_new_bundle_and_version = MagicMock()

    # WHEN adding a bundle and version which does not exist
    flow_cell_name: str = "flow_cell_name"
    demux_post_processing_api.add_bundle_and_version_if_non_existent(flow_cell_name=flow_cell_name)

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
    demux_post_processing_api.add_bundle_and_version_if_non_existent(flow_cell_name=flow_cell_name)

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


def test_add_sample_sheet(demultiplex_context: CGConfig, tmpdir_factory):
    # GIVEN a DemuxPostProcessing API
    demux_post_processing_api = DemuxPostProcessingAPI(demultiplex_context)
    demux_post_processing_api.add_file_if_non_existent = MagicMock()

    # GIVEN a flow cell directory and name
    flow_cell_directory: Path = Path(tmpdir_factory.mktemp("flow_cell_directory"))
    flow_cell_name = "flow_cell_name"

    # WHEN a sample sheet is added
    demux_post_processing_api.add_sample_sheet(
        flow_cell_directory=flow_cell_directory, flow_cell_name=flow_cell_name
    )

    # THEN add_file_if_non_existent was called with expected arguments
    expected_file_path = Path(
        flow_cell_directory, DemultiplexingDirsAndFiles.SAMPLE_SHEET_FILE_NAME
    )
    expected_tag_names = [SequencingFileTag.SAMPLE_SHEET, flow_cell_name]

    demux_post_processing_api.add_file_if_non_existent.assert_called_once_with(
        file_path=expected_file_path,
        flow_cell_name=flow_cell_name,
        tag_names=expected_tag_names,
    )


def test_add_fastq_files_with_sample_id(demultiplex_context: CGConfig, tmpdir_factory):
    # GIVEN a DemuxPostProcessing API
    demux_post_processing_api = DemuxPostProcessingAPI(demultiplex_context)

    demux_post_processing_api.get_sample_fastq_file_paths = MagicMock()
    demux_post_processing_api.get_sample_id_from_sample_fastq_file_path = MagicMock()
    demux_post_processing_api.add_file_if_non_existent = MagicMock()

    mock_fastq_paths = [
        Path(tmpdir_factory.mktemp("first_file.fastq.gz")),
        Path(tmpdir_factory.mktemp("second_file.fastq.gz")),
    ]
    demux_post_processing_api.get_sample_fastq_file_paths.return_value = mock_fastq_paths

    sample_id = "sample1"
    demux_post_processing_api.get_sample_id_from_sample_fastq_file_path.return_value = sample_id

    # GIVEN a flow cell directory and name
    flow_cell_directory: Path = Path(tmpdir_factory.mktemp("flow_cell_directory"))
    flow_cell_name = "flow_cell_name"

    # WHEN add_fastq_files is called
    demux_post_processing_api.add_sample_fastq_files(
        flow_cell_directory=flow_cell_directory, flow_cell_name=flow_cell_name
    )

    # THEN add_file_if_non_existent was called with expected arguments for each file
    expected_calls = [
        call(
            file_path=file_path,
            flow_cell_name=flow_cell_name,
            tag_names=[SequencingFileTag.FASTQ, sample_id],
        )
        for file_path in mock_fastq_paths
    ]

    demux_post_processing_api.add_file_if_non_existent.assert_has_calls(expected_calls)


def test_add_fastq_files_without_sample_id(demultiplex_context: CGConfig, tmpdir_factory):
    # GIVEN a DemuxPostProcessing API
    demux_post_processing_api = DemuxPostProcessingAPI(demultiplex_context)

    demux_post_processing_api.get_sample_id_from_sample_fastq_file_path = MagicMock()
    demux_post_processing_api.get_sample_id_from_sample_fastq_file_path.return_value = None

    demux_post_processing_api.add_file_if_non_existent = MagicMock()

    flow_cell_directory: Path = Path(tmpdir_factory.mktemp("flow_cell_directory"))
    flow_cell_name = "flow_cell_name"

    # WHEN add_fastq_files is called
    demux_post_processing_api.add_sample_fastq_files(
        flow_cell_directory=flow_cell_directory, flow_cell_name=flow_cell_name
    )

    # THEN add_file_if_non_existent was not called
    demux_post_processing_api.add_file_if_non_existent.assert_not_called()


def test_is_valid_sample_fastq_filename(demultiplex_context: CGConfig):
    # GIVEN a DemuxPostProcessing API
    demux_post_processing_api = DemuxPostProcessingAPI(demultiplex_context)

    # WHEN checking a filename containing "Undetermined"
    file_name = "Undetermined_file.fastq"
    assert not demux_post_processing_api.is_valid_sample_fastq_filename(file_name)

    # WHEN checking a valid filename
    file_name = "valid_file.fastq"
    assert demux_post_processing_api.is_valid_sample_fastq_filename(file_name)


def test_get_sample_fastq_file_paths(demultiplex_context: CGConfig, tmpdir_factory):
    # GIVEN a DemuxPostProcessing API
    demux_post_processing_api = DemuxPostProcessingAPI(demultiplex_context)

    # GIVEN some files in temporary directory
    tmp_dir = Path(tmpdir_factory.mktemp("data"))
    valid_file = tmp_dir / "file.fastq.gz"
    invalid_file = tmp_dir / "Undetermined_file.fastq.gz"
    valid_file.touch()
    invalid_file.touch()

    # WHEN we get sample fastq file paths
    result = demux_post_processing_api.get_sample_fastq_file_paths(tmp_dir)

    # THEN we should only get the valid file
    assert len(result) == 1
    assert valid_file in result
    assert invalid_file not in result


def test_get_sample_id_from_sample_fastq_file_path(demultiplex_context: CGConfig, tmpdir_factory):
    # GIVEN a DemuxPostProcessing API
    demux_post_processing_api = DemuxPostProcessingAPI(demultiplex_context)

    # GIVEN a sample directory and file
    tmp_dir = Path(tmpdir_factory.mktemp("flow_cell_directory"))
    sample_id = "sampleid"
    sample_dir = tmp_dir / f"prefix_{sample_id}"
    sample_dir.mkdir()
    sample_file = sample_dir / "file.fastq.gz"
    sample_file.touch()

    # WHEN we get sample id from sample fastq file path
    result = demux_post_processing_api.get_sample_id_from_sample_fastq_file_path(sample_file)

    # THEN we should get the correct sample id
    assert result == sample_id


def test_update_samples_with_read_counts_and_sequencing_date(demultiplex_context: CGConfig):
    """Test that samples can be updated with read counts and sequencing date."""

    # GIVEN a DemuxPostProcessing API
    demux_post_processing_api = DemuxPostProcessingAPI(demultiplex_context)

    demux_post_processing_api.status_db.get_sample_by_internal_id = MagicMock()
    demux_post_processing_api.status_db.get_number_of_reads_for_sample_from_metrics = MagicMock()

    mock_sample = MagicMock()
    mock_read_count = 1_000

    demux_post_processing_api.status_db.get_sample_by_internal_id.return_value = mock_sample
    demux_post_processing_api.status_db.get_number_of_reads_for_sample_from_metrics.return_value = (
        mock_read_count
    )

    # GIVEN a list of internal sample IDs
    sample_ids = ["sample1", "sample2"]

    # WHEN calling the method with the sample IDs
    demux_post_processing_api.update_sample_read_counts(sample_ids)

    # THEN the read count was set on the mock sample
    assert mock_sample.reads == mock_read_count
