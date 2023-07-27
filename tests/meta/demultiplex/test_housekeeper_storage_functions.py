"""Tests for the housekeeper storage functions of the demultiplexing post post-processing module."""
from pathlib import Path
from typing import List
from mock import MagicMock, call

from cg.constants.housekeeper_tags import SequencingFileTag
from cg.meta.demultiplex.demux_post_processing import DemuxPostProcessingAPI

from cg.models.cg_config import CGConfig

from cg.models.demultiplex.flow_cell import FlowCellDirectoryData

from cg.meta.demultiplex.housekeeper_storage_functions import (
    add_bundle_and_version_if_non_existent,
    add_tags_if_non_existent,
    add_sample_fastq_files_to_housekeeper,
    add_sample_sheet_path_to_housekeeper,
    add_demux_logs_to_housekeeper,
)


def test_add_bundle_and_version_if_non_existent(demultiplex_context: CGConfig):
    # GIVEN a DemuxPostProcessing API
    demux_post_processing_api = DemuxPostProcessingAPI(demultiplex_context)

    demux_post_processing_api.hk_api.bundle = MagicMock(return_value=None)
    demux_post_processing_api.hk_api.create_new_bundle_and_version = MagicMock()

    # WHEN adding a bundle and version which does not exist
    flow_cell_name: str = "flow_cell_name"
    add_bundle_and_version_if_non_existent(
        bundle_name=flow_cell_name, hk_api=demux_post_processing_api.hk_api
    )

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
    add_bundle_and_version_if_non_existent(
        bundle_name=flow_cell_name, hk_api=demux_post_processing_api.hk_api
    )
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
    add_tags_if_non_existent(tag_names=tag_names, hk_api=demux_post_processing_api.hk_api)

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
    add_tags_if_non_existent(tag_names=tag_names, hk_api=demux_post_processing_api.hk_api)

    # Assert that the expected methods were called with the expected arguments
    demux_post_processing_api.hk_api.get_tag.assert_has_calls(
        [call(name="tag1"), call(name="tag2")]
    )
    demux_post_processing_api.hk_api.add_tag.assert_not_called()


def test_add_fastq_files_without_sample_id(
    demultiplex_context: CGConfig, dragen_flow_cell: FlowCellDirectoryData
):
    # GIVEN a DemuxPostProcessing API
    demux_post_processing_api = DemuxPostProcessingAPI(demultiplex_context)

    demux_post_processing_api.add_file_to_bundle_if_non_existent = MagicMock()

    # WHEN add_fastq_files is called

    add_sample_fastq_files_to_housekeeper(
        flow_cell=dragen_flow_cell,
        hk_api=demux_post_processing_api.hk_api,
        store=demux_post_processing_api.status_db,
    )

    # THEN add_file_if_non_existent was not called
    demux_post_processing_api.add_file_to_bundle_if_non_existent.assert_not_called()


def test_add_existing_sample_sheet(
    demultiplex_context: CGConfig, dragen_flow_cell: FlowCellDirectoryData, novaseq_6000_dir: Path
):
    # GIVEN a DemuxPostProcessing API
    demux_post_processing_api = DemuxPostProcessingAPI(demultiplex_context)

    # GIVEN a flow cell directory and name
    flow_cell_directory = Path(novaseq_6000_dir, dragen_flow_cell.full_name)

    # GIVEN that a flow cell bundle exists in Housekeeper
    add_bundle_and_version_if_non_existent(
        bundle_name=dragen_flow_cell.id, hk_api=demux_post_processing_api.hk_api
    )

    # WHEN a sample sheet is added
    add_sample_sheet_path_to_housekeeper(
        flow_cell_directory=flow_cell_directory,
        flow_cell_name=dragen_flow_cell.id,
        hk_api=demux_post_processing_api.hk_api,
    )

    # THEN a sample sheet file was added to the bundle
    expected_tag_names = [SequencingFileTag.SAMPLE_SHEET, dragen_flow_cell.id]

    files = demux_post_processing_api.hk_api.get_files(
        bundle=dragen_flow_cell.id, tags=expected_tag_names
    ).all()
    assert len(files) == 1


def test_add_demux_logs_to_housekeeper(
    demultiplex_context: CGConfig, dragen_flow_cell: FlowCellDirectoryData
):
    # GIVEN a DemuxPostProcessing API
    demux_post_processing_api = DemuxPostProcessingAPI(demultiplex_context)

    # GIVEN a bundle and flow cell version exists in housekeeper
    add_bundle_and_version_if_non_existent(
        bundle_name=dragen_flow_cell.id, hk_api=demux_post_processing_api.hk_api
    )

    # GIVEN a demux log in the run directory
    demux_log_file_paths: List[Path] = [
        Path(
            demux_post_processing_api.demux_api.run_dir,
            f"{dragen_flow_cell.full_name}",
            f"{dragen_flow_cell.id}_demultiplex.stdout",
        ),
        Path(
            demux_post_processing_api.demux_api.run_dir,
            f"{dragen_flow_cell.full_name}",
            f"{dragen_flow_cell.id}_demultiplex.stderr",
        ),
    ]
    for file_path in demux_log_file_paths:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.touch()

    # WHEN adding the demux logs to housekeeper
    add_demux_logs_to_housekeeper(
        flow_cell=dragen_flow_cell,
        flow_cell_run_dir=demux_post_processing_api.demux_api.run_dir,
        hk_api=demux_post_processing_api.hk_api,
    )

    # THEN the demux log was added to housekeeper
    files = demux_post_processing_api.hk_api.get_files(
        tags=[SequencingFileTag.DEMUX_LOG],
        bundle=dragen_flow_cell.id,
    ).all()

    expected_file_names: List[str] = []
    for file_path in demux_log_file_paths:
        expected_file_names.append(file_path.name.split("/")[-1])

    # THEN the demux logs were added to housekeeper with the correct names
    assert len(files) == 2
    for file in files:
        assert file.path.split("/")[-1] in expected_file_names
