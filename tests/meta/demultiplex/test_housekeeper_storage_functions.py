"""Tests for the housekeeper storage functions of the demultiplexing post post-processing module."""

from pathlib import Path

from housekeeper.store.models import File
from mock import MagicMock, call

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.housekeeper_tags import SequencingFileTag
from cg.meta.demultiplex.demux_post_processing import DemuxPostProcessingAPI
from cg.meta.demultiplex.housekeeper_storage_functions import (
    add_demux_logs_to_housekeeper,
    add_sample_fastq_files_to_housekeeper,
    add_sample_sheet_path_to_housekeeper,
)
from cg.models.cg_config import CGConfig
from cg.models.flow_cell.flow_cell import FlowCellDirectoryData


def test_add_bundle_and_version_if_non_existent(demultiplex_context: CGConfig):
    # GIVEN a DemuxPostProcessing API
    demux_post_processing_api = DemuxPostProcessingAPI(demultiplex_context)

    demux_post_processing_api.hk_api.bundle = MagicMock(return_value=None)
    demux_post_processing_api.hk_api.create_new_bundle_and_version = MagicMock()

    # WHEN adding a bundle and version which does not exist
    flow_cell_name: str = "flow_cell_name"
    demux_post_processing_api.hk_api.add_bundle_and_version_if_non_existent(flow_cell_name)

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
    demux_post_processing_api.hk_api.add_bundle_and_version_if_non_existent(flow_cell_name)
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
    demux_post_processing_api.hk_api.add_tags_if_non_existent(tag_names)

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
    demux_post_processing_api.hk_api.add_tags_if_non_existent(tag_names)

    # Assert that the expected methods were called with the expected arguments
    demux_post_processing_api.hk_api.get_tag.assert_has_calls(
        [call(name="tag1"), call(name="tag2")]
    )
    demux_post_processing_api.hk_api.add_tag.assert_not_called()


def test_add_fastq_files_without_sample_id(
    demultiplex_context: CGConfig, bcl_convert_flow_cell: FlowCellDirectoryData
):
    # GIVEN a DemuxPostProcessing API
    demux_post_processing_api = DemuxPostProcessingAPI(demultiplex_context)

    # GIVEN that the sample sheet exists in housekeeper and the path is in the flow cell
    add_sample_sheet_path_to_housekeeper(
        flow_cell_directory=bcl_convert_flow_cell.path,
        flow_cell_name=bcl_convert_flow_cell.id,
        hk_api=demultiplex_context.housekeeper_api,
    )
    sample_sheet_path: Path = demultiplex_context.housekeeper_api.get_sample_sheet_path(
        bcl_convert_flow_cell.id
    )

    bcl_convert_flow_cell.set_sample_sheet_path_hk(sample_sheet_path)
    demux_post_processing_api.hk_api.add_file_to_bundle_if_non_existent = MagicMock()

    # WHEN adding the fastq files to housekeeper
    add_sample_fastq_files_to_housekeeper(
        flow_cell=bcl_convert_flow_cell,
        hk_api=demux_post_processing_api.hk_api,
        store=demux_post_processing_api.status_db,
    )

    # THEN no files were added to housekeeper
    demux_post_processing_api.hk_api.add_file_to_bundle_if_non_existent.assert_not_called()


def test_add_existing_sample_sheet(
    demultiplex_context: CGConfig,
    bcl_convert_flow_cell: FlowCellDirectoryData,
    tmp_flow_cells_directory: Path,
):
    # GIVEN a DemuxPostProcessing API
    demux_post_processing_api = DemuxPostProcessingAPI(demultiplex_context)

    # GIVEN a flow cell directory and name
    flow_cell_directory = Path(tmp_flow_cells_directory, bcl_convert_flow_cell.full_name)

    # GIVEN that a flow cell bundle exists in Housekeeper
    demux_post_processing_api.hk_api.add_bundle_and_version_if_non_existent(
        bundle_name=bcl_convert_flow_cell.id
    )

    # WHEN a sample sheet is added
    add_sample_sheet_path_to_housekeeper(
        flow_cell_directory=flow_cell_directory,
        flow_cell_name=bcl_convert_flow_cell.id,
        hk_api=demux_post_processing_api.hk_api,
    )

    # THEN a sample sheet file was added to the bundle
    expected_tag_names = [SequencingFileTag.SAMPLE_SHEET, bcl_convert_flow_cell.id]

    files = demux_post_processing_api.hk_api.get_files(
        bundle=bcl_convert_flow_cell.id, tags=expected_tag_names
    ).all()
    assert len(files) == 1


def test_add_demux_logs_to_housekeeper(
    demultiplex_context: CGConfig, bcl_convert_flow_cell: FlowCellDirectoryData
):
    # GIVEN a DemuxPostProcessing API
    demux_post_processing_api = DemuxPostProcessingAPI(demultiplex_context)

    # GIVEN a bundle and flow cell version exists in housekeeper
    demux_post_processing_api.hk_api.add_bundle_and_version_if_non_existent(
        bundle_name=bcl_convert_flow_cell.id
    )

    # GIVEN a demux log in the run directory
    demux_log_file_paths: list[Path] = [
        Path(
            demux_post_processing_api.flow_cells_dir,
            f"{bcl_convert_flow_cell.full_name}",
            f"{bcl_convert_flow_cell.id}_demultiplex.stdout",
        ),
        Path(
            demux_post_processing_api.flow_cells_dir,
            f"{bcl_convert_flow_cell.full_name}",
            f"{bcl_convert_flow_cell.id}_demultiplex.stderr",
        ),
    ]
    for file_path in demux_log_file_paths:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.touch()

    # WHEN adding the demux logs to housekeeper
    add_demux_logs_to_housekeeper(
        flow_cell=bcl_convert_flow_cell,
        flow_cell_run_dir=demux_post_processing_api.flow_cells_dir,
        hk_api=demux_post_processing_api.hk_api,
    )

    # THEN the demux log was added to housekeeper
    files = demux_post_processing_api.hk_api.get_files(
        tags=[SequencingFileTag.DEMUX_LOG],
        bundle=bcl_convert_flow_cell.id,
    ).all()

    expected_file_names: list[str] = []
    for file_path in demux_log_file_paths:
        expected_file_names.append(file_path.name.split("/")[-1])

    # THEN the demux logs were added to housekeeper with the correct names
    assert len(files) == 2
    for file in files:
        assert file.path.split("/")[-1] in expected_file_names


def test_store_fastq_path_in_housekeeper_correct_tags(
    populated_housekeeper_api: HousekeeperAPI,
    empty_fastq_file_path: Path,
    novaseq6000_flow_cell: FlowCellDirectoryData,
):
    """Test that a fastq file is stored in Housekeeper with the correct tags."""
    sample_id: str = "sample_internal_id"
    # GIVEN a fastq file that has not been added to Housekeeper
    assert not populated_housekeeper_api.files(path=empty_fastq_file_path.as_posix()).first()

    # WHEN adding the fastq file to housekeeper
    populated_housekeeper_api.store_fastq_path_in_housekeeper(
        sample_internal_id=sample_id,
        sample_fastq_path=empty_fastq_file_path,
        flow_cell_id=novaseq6000_flow_cell.id,
    )

    # THEN the file was added to Housekeeper with the correct tags
    file: File = populated_housekeeper_api.get_files(bundle=sample_id).first()
    expected_tags: set[str] = {SequencingFileTag.FASTQ.value, novaseq6000_flow_cell.id, sample_id}
    assert {tag.name for tag in file.tags} == expected_tags
