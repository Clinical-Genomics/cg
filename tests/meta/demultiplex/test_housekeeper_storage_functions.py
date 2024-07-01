"""Tests for the housekeeper storage functions of the demultiplexing post post-processing module."""

from pathlib import Path

import pytest
from housekeeper.store.models import File
from mock import MagicMock, call

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.constants.housekeeper_tags import SequencingFileTag
from cg.meta.demultiplex.demux_post_processing import DemuxPostProcessingAPI
from cg.meta.demultiplex.housekeeper_storage_functions import (
    add_and_include_sample_sheet_path_to_housekeeper,
    add_demux_logs_to_housekeeper,
    add_run_parameters_file_to_housekeeper,
    add_sample_fastq_files_to_housekeeper,
    delete_sequencing_data_from_housekeeper,
)
from cg.models.cg_config import CGConfig
from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData
from tests.store_helpers import StoreHelpers


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
    demultiplex_context: CGConfig, novaseq_6000_post_1_5_kits_flow_cell: IlluminaRunDirectoryData
):
    # GIVEN a DemuxPostProcessing API
    demux_post_processing_api = DemuxPostProcessingAPI(demultiplex_context)

    # GIVEN that the sample sheet exists in housekeeper and the path is in the flow cell
    add_and_include_sample_sheet_path_to_housekeeper(
        flow_cell_directory=novaseq_6000_post_1_5_kits_flow_cell.path,
        flow_cell_name=novaseq_6000_post_1_5_kits_flow_cell.id,
        hk_api=demultiplex_context.housekeeper_api,
    )
    sample_sheet_path: Path = demultiplex_context.housekeeper_api.get_sample_sheet_path(
        novaseq_6000_post_1_5_kits_flow_cell.id
    )

    novaseq_6000_post_1_5_kits_flow_cell.set_sample_sheet_path_hk(sample_sheet_path)
    demux_post_processing_api.hk_api.add_file_to_bundle_if_non_existent = MagicMock()

    # WHEN adding the fastq files to housekeeper
    add_sample_fastq_files_to_housekeeper(
        flow_cell=novaseq_6000_post_1_5_kits_flow_cell,
        hk_api=demux_post_processing_api.hk_api,
        store=demux_post_processing_api.status_db,
    )

    # THEN no files were added to housekeeper
    demux_post_processing_api.hk_api.add_file_to_bundle_if_non_existent.assert_not_called()


def test_add_existing_sample_sheet(
    demultiplex_context: CGConfig,
    novaseq_6000_post_1_5_kits_flow_cell: IlluminaRunDirectoryData,
    tmp_illumina_sequencing_runs_directory: Path,
):
    # GIVEN a DemuxPostProcessing API
    demux_post_processing_api = DemuxPostProcessingAPI(demultiplex_context)

    # GIVEN a flow cell directory and name
    flow_cell_directory = Path(
        tmp_illumina_sequencing_runs_directory, novaseq_6000_post_1_5_kits_flow_cell.full_name
    )

    # GIVEN that a flow cell bundle exists in Housekeeper
    demux_post_processing_api.hk_api.add_bundle_and_version_if_non_existent(
        bundle_name=novaseq_6000_post_1_5_kits_flow_cell.id
    )

    # WHEN a sample sheet is added
    add_and_include_sample_sheet_path_to_housekeeper(
        flow_cell_directory=flow_cell_directory,
        flow_cell_name=novaseq_6000_post_1_5_kits_flow_cell.id,
        hk_api=demux_post_processing_api.hk_api,
    )

    # THEN a sample sheet file was added to the bundle
    expected_tag_names = [SequencingFileTag.SAMPLE_SHEET, novaseq_6000_post_1_5_kits_flow_cell.id]

    files = demux_post_processing_api.hk_api.get_files(
        bundle=novaseq_6000_post_1_5_kits_flow_cell.id, tags=expected_tag_names
    ).all()
    assert len(files) == 1


def test_add_demux_logs_to_housekeeper(
    demultiplex_context: CGConfig, novaseq_6000_post_1_5_kits_flow_cell: IlluminaRunDirectoryData
):
    # GIVEN a DemuxPostProcessing API
    demux_post_processing_api = DemuxPostProcessingAPI(demultiplex_context)

    # GIVEN a bundle and flow cell version exists in housekeeper
    demux_post_processing_api.hk_api.add_bundle_and_version_if_non_existent(
        bundle_name=novaseq_6000_post_1_5_kits_flow_cell.id
    )

    # GIVEN a demux log in the run directory
    demux_log_file_paths: list[Path] = [
        Path(
            demux_post_processing_api.flow_cells_dir,
            f"{novaseq_6000_post_1_5_kits_flow_cell.full_name}",
            f"{novaseq_6000_post_1_5_kits_flow_cell.id}_demultiplex.stdout",
        ),
        Path(
            demux_post_processing_api.flow_cells_dir,
            f"{novaseq_6000_post_1_5_kits_flow_cell.full_name}",
            f"{novaseq_6000_post_1_5_kits_flow_cell.id}_demultiplex.stderr",
        ),
    ]
    for file_path in demux_log_file_paths:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.touch()

    # WHEN adding the demux logs to housekeeper
    add_demux_logs_to_housekeeper(
        flow_cell=novaseq_6000_post_1_5_kits_flow_cell,
        flow_cell_run_dir=demux_post_processing_api.flow_cells_dir,
        hk_api=demux_post_processing_api.hk_api,
    )

    # THEN the demux log was added to housekeeper
    files = demux_post_processing_api.hk_api.get_files(
        tags=[SequencingFileTag.DEMUX_LOG],
        bundle=novaseq_6000_post_1_5_kits_flow_cell.id,
    ).all()

    expected_file_names: list[str] = []
    for file_path in demux_log_file_paths:
        expected_file_names.append(file_path.name.split("/")[-1])

    # THEN the demux logs were added to housekeeper with the correct names
    assert len(files) == 2
    for file in files:
        assert file.path.split("/")[-1] in expected_file_names


def test_add_run_parameters_to_housekeeper(
    demultiplex_context: CGConfig, novaseq_x_flow_cell: IlluminaRunDirectoryData
):
    """Test that the run parameters file of a flow cell is added to Housekeeper."""
    # GIVEN a flow cell with a run parameters file and a Housekeeper API
    hk_api = demultiplex_context.housekeeper_api

    # GIVEN that a run parameters file does not exist for the flow cell in Housekeeper
    assert not hk_api.files(tags=[SequencingFileTag.RUN_PARAMETERS, novaseq_x_flow_cell.id]).all()

    # GIVEN that a bundle and version exists in housekeeper
    hk_api.add_bundle_and_version_if_non_existent(bundle_name=novaseq_x_flow_cell.id)

    # WHEN adding the run parameters file to housekeeper
    add_run_parameters_file_to_housekeeper(
        flow_cell_name=novaseq_x_flow_cell.full_name,
        flow_cell_run_dir=demultiplex_context.demultiplex_api.sequencing_runs_dir,
        hk_api=hk_api,
    )

    # THEN the run parameters file was added to housekeeper
    run_parameters_file: File = hk_api.files(
        tags=[SequencingFileTag.RUN_PARAMETERS, novaseq_x_flow_cell.id]
    ).first()
    assert run_parameters_file.path.endswith(DemultiplexingDirsAndFiles.RUN_PARAMETERS_PASCAL_CASE)


def test_store_fastq_path_in_housekeeper_correct_tags(
    populated_housekeeper_api: HousekeeperAPI,
    empty_fastq_file_path: Path,
    novaseq_6000_post_1_5_kits_flow_cell_id: str,
):
    """Test that a fastq file is stored in Housekeeper with the correct tags."""
    sample_id: str = "sample_internal_id"
    # GIVEN a fastq file that has not been added to Housekeeper
    assert not populated_housekeeper_api.files(path=empty_fastq_file_path.as_posix()).first()

    # WHEN adding the fastq file to housekeeper
    populated_housekeeper_api.store_fastq_path_in_housekeeper(
        sample_internal_id=sample_id,
        sample_fastq_path=empty_fastq_file_path,
        flow_cell_id=novaseq_6000_post_1_5_kits_flow_cell_id,
    )

    # THEN the file was added to Housekeeper with the correct tags
    file: File = populated_housekeeper_api.get_files(bundle=sample_id).first()
    expected_tags: set[str] = {
        SequencingFileTag.FASTQ.value,
        novaseq_6000_post_1_5_kits_flow_cell_id,
        sample_id,
    }
    assert {tag.name for tag in file.tags} == expected_tags


@pytest.mark.parametrize(
    "file_tag",
    [SequencingFileTag.FASTQ, SequencingFileTag.SPRING, SequencingFileTag.SPRING_METADATA],
)
def test_delete_sequencing_data_from_housekeeper(
    file_tag: str,
    populated_housekeeper_api,
    flow_cell_name: str,
    tmp_path: Path,
    helpers: StoreHelpers,
):
    """Tests that each type of sequencing file is removed when deleting them from Housekeeper."""
    # GIVEN a sample with sequencing files from a flow cell
    sample_id: str = "new_sample"
    helpers.quick_hk_bundle(
        store=populated_housekeeper_api,
        bundle_name=sample_id,
        files=[tmp_path],
        tags=[[file_tag, flow_cell_name, sample_id]],
    )
    assert populated_housekeeper_api.files(bundle=sample_id, tags={file_tag}).all()

    # WHEN deleting the sequencing data from housekeeper
    delete_sequencing_data_from_housekeeper(
        flow_cell_id=flow_cell_name, hk_api=populated_housekeeper_api
    )

    # THEN the sequencing data is deleted from housekeeper
    assert not populated_housekeeper_api.files(bundle=sample_id, tags={file_tag}).all()


def test_delete_sequencing_data_from_housekeeper_two_flow_cells(
    real_housekeeper_api: HousekeeperAPI,
    flow_cell_name: str,
    tmp_path: Path,
    helpers: StoreHelpers,
):
    """Tests that the delete_sequencing_data_from_housekeeper function deletes the correct files
    from housekeeper when there are files from two flow cells."""
    # GIVEN a sample with sequencing files from two flow cells
    sample_id: str = "new_sample"
    second_file: Path = tmp_path.with_suffix(".2.fastq.gz")
    second_file.touch()
    second_flow_cell_name: str = "second-flow-cell"
    helpers.quick_hk_bundle(
        store=real_housekeeper_api,
        bundle_name=sample_id,
        files=[tmp_path, second_file],
        tags=[
            [SequencingFileTag.FASTQ, flow_cell_name, sample_id],
            [SequencingFileTag.FASTQ, second_flow_cell_name, sample_id],
        ],
    )
    assert (
        len(real_housekeeper_api.files(bundle=sample_id, tags={SequencingFileTag.FASTQ}).all()) == 2
    )

    # WHEN deleting the sequencing data of one flow cell from housekeeper
    delete_sequencing_data_from_housekeeper(
        flow_cell_id=flow_cell_name, hk_api=real_housekeeper_api
    )

    # THEN the sequencing data the first flow cell is deleted from housekeeper
    assert not real_housekeeper_api.files(bundle=sample_id, tags={flow_cell_name}).all()

    # THEN the sequencing data from the second flow cell should remain
    remaining_file: File = real_housekeeper_api.files(bundle=sample_id).one()
    assert remaining_file
    assert remaining_file.path.endswith(second_file.name)
