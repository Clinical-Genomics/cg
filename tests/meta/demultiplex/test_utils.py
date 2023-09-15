from pathlib import Path
from typing import List

import pytest

from cg.constants.constants import FileExtensions
from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.constants.sequencing import FLOWCELL_Q30_THRESHOLD, Sequencers
from cg.exc import FlowCellError
from cg.meta.demultiplex.utils import (
    add_flow_cell_name_to_fastq_file_path,
    create_delivery_file_in_flow_cell_directory,
    get_lane_from_sample_fastq,
    get_q30_threshold,
    get_sample_sheet_path,
    get_undetermined_fastqs,
    is_file_path_compressed_fastq,
    is_file_relevant_for_demultiplexing,
    is_lane_in_fastq_file_name,
    is_sample_id_in_directory_name,
    is_syncing_complete,
    is_valid_sample_fastq_file,
    parse_flow_cell_directory_data,
    parse_manifest_file,
)
from cg.models.demultiplex.flow_cell import FlowCellDirectoryData


def test_validate_sample_fastq_with_valid_file():
    # GIVEN a sample fastq file with a lane number and sample id in the parent directory name
    sample_fastq = Path("Sample_123/sample_L0002.fastq.gz")

    # WHEN validating the sample fastq file
    is_valid_fastq: bool = is_valid_sample_fastq_file(
        sample_fastq=sample_fastq, sample_internal_id="sample"
    )

    # THEN it should be valid
    assert is_valid_fastq


def test_validate_sample_fastq_without_sample_id_in_parent_directory_name():
    # GIVEN a sample fastq file without a sample id in the parent directory name or file name
    sample_fastq = Path("L0002.fastq.gz")

    # WHEN validating the sample fastq file
    is_valid_fastq: bool = is_valid_sample_fastq_file(
        sample_fastq=sample_fastq, sample_internal_id="sample_id"
    )

    # THEN it should not be valid
    assert not is_valid_fastq


def test_validate_sample_fastq_without_lane_number_in_path():
    # GIVEN a sample fastq file without a lane number
    sample_fastq = Path("Sample_123/sample_id.fastq.gz")

    # WHEN validating the sample fastq file
    is_valid_fastq: bool = is_valid_sample_fastq_file(sample_fastq, sample_internal_id="sample_id")

    # THEN it should not be valid
    assert not is_valid_fastq


def test_validate_sample_fastq_with_invalid_file_extension():
    # GIVEN a sample fastq file without a valid file extension
    sample_fastq = Path("Sample_123/123_L0002.fastq")

    # WHEN validating the sample fastq file
    is_valid_fastq: bool = is_valid_sample_fastq_file(sample_fastq, sample_internal_id="123")

    # THEN it should not be valid
    assert not is_valid_fastq


def test_is_file_path_compressed_fastq_with_valid_file():
    # GIVEN a valid .fastq.gz file
    file_path = Path("sample_L0002.fastq.gz")

    # WHEN checking if the file path is a compressed fastq file
    is_file_compressed: bool = is_file_path_compressed_fastq(file_path)

    # THEN the result should be True
    assert is_file_compressed


def test_is_file_path_compressed_fastq_with_invalid_file():
    # GIVEN a file with invalid extension
    file_path = Path("sample_L0002.fastq")

    # WHEN checking if the file path is a compressed fastq file
    is_file_compressed: bool = is_file_path_compressed_fastq(file_path)

    # THEN the result should be False
    assert not is_file_compressed


def test_is_lane_in_fastq_file_name_with_valid_file():
    # GIVEN a valid file containing lane number
    file_path = Path("sample_L0002.fastq.gz")

    # WHEN checking if the lane number is in the fastq file name
    is_lane_in_name: bool = is_lane_in_fastq_file_name(file_path)

    # THEN the result should be True
    assert is_lane_in_name


def test_is_lane_in_fastq_file_name_with_invalid_file():
    # GIVEN a file without lane number
    file_path = Path("sample.fastq.gz")

    # WHEN checking if the lane number is in the fastq file name
    is_lane_in_name: bool = is_lane_in_fastq_file_name(file_path)

    # THEN the result should be False
    assert not is_lane_in_name


def test_is_sample_id_in_directory_name_with_valid_directory():
    # GIVEN a directory containing sample id
    directory = Path("Sample_123")

    # WHEN checking if the sample id is in the directory name
    is_sample_id_in_dir: bool = is_sample_id_in_directory_name(
        directory=directory, sample_internal_id="123"
    )

    # THEN the result should be True
    assert is_sample_id_in_dir


def test_is_sample_id_in_directory_name_with_invalid_directory():
    # GIVEN a directory without sample id
    directory = Path("sample/123_L0002.fastq.gz")

    # WHEN checking if the sample id is in the directory name
    is_sample_id_in_dir: bool = is_sample_id_in_directory_name(
        directory=directory, sample_internal_id="sample_id"
    )

    # THEN the result should be False
    assert is_sample_id_in_dir is False


def test_get_lane_from_sample_fastq_file_path():
    # GIVEN a sample fastq path
    initial_lane: int = 4
    sample_fastq_path = Path(
        f"H5CYFDSX7_ACC12164A17_S367_L00{initial_lane}"
        f"_R1_001{FileExtensions.FASTQ}{FileExtensions.GZIP}"
    )

    # WHEN we get lane from the sample fastq file path
    result_lane: int = get_lane_from_sample_fastq(sample_fastq_path)

    # THEN we should get the correct lane
    assert result_lane == initial_lane


def test_get_lane_from_sample_fastq_file_path_no_flowcell():
    # GIVEN a sample fastq path without a flow cell id
    initial_lane: int = 4
    sample_fastq_path = Path(
        f"ACC12164A17_S367_L00{initial_lane}_R1_001{FileExtensions.FASTQ}{FileExtensions.GZIP}",
    )

    # WHEN we get lane from the sample fastq file path
    result_lane: int = get_lane_from_sample_fastq(sample_fastq_path)

    # THEN we should get the correct lane
    assert result_lane == initial_lane


def test_validate_demux_complete_flow_cell_directory_when_it_exists(tmp_path: Path):
    # GIVEN a temporary directory as the flow cell directory with a demux complete file
    flow_cell_directory: Path = tmp_path
    Path(flow_cell_directory, DemultiplexingDirsAndFiles.DEMUX_COMPLETE).touch()

    # WHEN the create_delivery_file_in_flow_cell_directory function is called
    create_delivery_file_in_flow_cell_directory(flow_cell_directory)

    # THEN a delivery file should exist in the flow cell directory
    assert (flow_cell_directory / DemultiplexingDirsAndFiles.DEMUX_COMPLETE).exists()


def test_validate_demux_complete_flow_cell_directory_when_it_does_not_exist(tmp_path: Path):
    # GIVEN a temporary directory as the flow cell directory without a demux complete file
    flow_cell_directory: Path = tmp_path

    # WHEN the create_delivery_file_in_flow_cell_directory function is called
    create_delivery_file_in_flow_cell_directory(flow_cell_directory)

    # THEN a delivery file should not exist in the flow cell directory
    assert not (flow_cell_directory / DemultiplexingDirsAndFiles.DEMUX_COMPLETE).exists()


def test_get_q30_threshold():
    # GIVEN a specific sequencer type
    sequencer_type: Sequencers = Sequencers.HISEQGA

    # WHEN getting the Q30 threshold for the sequencer type
    q30_threshold: int = get_q30_threshold(sequencer_type)

    # THEN the correct Q30 threshold should be returned
    assert q30_threshold == FLOWCELL_Q30_THRESHOLD[sequencer_type]


def test_get_sample_sheet_path_found(tmp_path: Path):
    # GIVEN a temporary directory as the flow cell directory
    flow_cell_directory: Path = tmp_path

    # GIVEN a sample sheet file in the flow cell directory
    sample_sheet_path = Path(flow_cell_directory, DemultiplexingDirsAndFiles.SAMPLE_SHEET_FILE_NAME)
    sample_sheet_path.touch()

    # WHEN the sample sheet is retrieved
    found_sample_sheet_path: Path = get_sample_sheet_path(flow_cell_directory)

    # THEN the path to the sample sheet file should be returned
    assert found_sample_sheet_path == sample_sheet_path


def test_get_sample_sheet_path_found_in_nested_directory(tmp_path: Path):
    # GIVEN a temporary directory as the flow cell directory
    flow_cell_directory: Path = tmp_path

    # GIVEN a nested directory within the flow cell directory
    nested_directory = Path(flow_cell_directory, "nested")
    nested_directory.mkdir()

    # GIVEN a sample sheet file in the nested directory
    sample_sheet_path = Path(nested_directory, DemultiplexingDirsAndFiles.SAMPLE_SHEET_FILE_NAME)
    sample_sheet_path.touch()

    # WHEN the sample sheet is retrieved
    found_sample_sheet_path: Path = get_sample_sheet_path(flow_cell_directory)

    # THEN the path to the sample sheet file should be returned
    assert found_sample_sheet_path == sample_sheet_path


def test_get_sample_sheet_path_not_found(tmp_path: Path):
    # GIVEN a temporary directory as the flow cell directory without a sample sheet file
    flow_cell_directory: Path = tmp_path

    # WHEN the sample sheet is retrieved
    # THEN a FileNotFoundError should be raised
    with pytest.raises(FileNotFoundError):
        get_sample_sheet_path(flow_cell_directory)


def test_parse_flow_cell_directory_data_invalid():
    with pytest.raises(FlowCellError):
        parse_flow_cell_directory_data(Path("dummy_path"), "dummy_bcl_converter")


def test_parse_flow_cell_directory_data_valid():
    # GIVEN a flow cell directory which is valid
    # WHEN parsing the flow cell directory data
    flow_cell_run_directory = "20230508_LH00188_0003_A22522YLT3"
    result = parse_flow_cell_directory_data(Path(flow_cell_run_directory), "dummy_bcl_converter")

    # THEN a FlowCellDirectoryData object should be returned
    assert isinstance(result, FlowCellDirectoryData)

    # THEN the flow cell path and bcl converter should be set
    assert result.path == Path(flow_cell_run_directory)
    assert result.bcl_converter == "dummy_bcl_converter"


def test_parse_manifest_file(novaseq_x_manifest_file: Path):
    # GIVEN a manifest file

    # WHEN parsing the manifest file
    files_at_source: List[Path] = parse_manifest_file(novaseq_x_manifest_file)

    # THEN paths should be returned
    # THEN the paths should be Path objects
    assert files_at_source
    assert isinstance(files_at_source, list)
    assert all(isinstance(file, Path) for file in files_at_source)


@pytest.mark.parametrize(
    "file, expected_result",
    [
        (Path("flow_cell_dir", DemultiplexingDirsAndFiles.DATA, "some_file.txt"), True),
        (Path("flow_cell_dir", DemultiplexingDirsAndFiles.INTER_OP, "some_file.txt"), True),
        (Path("flow_cell_dir", "Thumbnail_Images", "some_file.txt"), False),
    ],
)
def test_is_file_relevant_for_demultiplexing(file: Path, expected_result: bool):
    # GIVEN a file path

    # WHEN checking if the file is relevant
    result = is_file_relevant_for_demultiplexing(file)

    # THEN the correct result should be returned
    assert result == expected_result


def test_is_syncing_complete_true(lsyncd_source_directory: Path, lsyncd_target_directory: Path):
    # GIVEN a source directory with a manifest file

    # GIVEN a target directory with all relevant files

    # WHEN checking if the syncing is complete
    is_directory_synced: bool = is_syncing_complete(
        source_directory=lsyncd_source_directory, target_directory=lsyncd_target_directory
    )

    # THEN the syncing should be deemed complete
    assert is_directory_synced


def test_is_syncing_complete_false(
    lsyncd_source_directory: Path, lsyncd_target_directory: Path, base_call_file: Path
):
    """Tests if the syncing is not complete when a file is missing."""
    # GIVEN a source directory with a manifest file

    # GIVEN a target directory without all relevant files
    Path(lsyncd_target_directory, base_call_file).unlink()

    # WHEN checking if the syncing is complete
    is_directory_synced: bool = is_syncing_complete(
        source_directory=lsyncd_source_directory, target_directory=lsyncd_target_directory
    )

    # THEN the syncing should not be deemed complete
    assert not is_directory_synced


def test_add_flow_cell_name_to_fastq_file_path(
    bcl2fastq_flow_cell_id: str, demultiplex_fastq_file_path
):
    # GIVEN a fastq file path and a flow cell name

    # WHEN adding the flow cell name to the fastq file path
    rename_fastq_file_path: Path = add_flow_cell_name_to_fastq_file_path(
        fastq_file_path=demultiplex_fastq_file_path, flow_cell_name=bcl2fastq_flow_cell_id
    )

    # THEN the fastq file path should be returned with the flow cell name added
    assert rename_fastq_file_path == Path(
        demultiplex_fastq_file_path.parent,
        f"{bcl2fastq_flow_cell_id}_{demultiplex_fastq_file_path.name}",
    )


def test_add_flow_cell_name_to_fastq_file_path_when_flow_cell_name_already_in_name(
    bcl2fastq_flow_cell_id: str, demultiplex_fastq_file_path
):
    # GIVEN a fastq file path and a flow cell name

    # GIVEN that the flow cell name is already in the fastq file path
    demultiplex_fastq_file_path = Path(
        f"{bcl2fastq_flow_cell_id}_{demultiplex_fastq_file_path.name}"
    )

    # WHEN adding the flow cell name to the fastq file path
    renamed_fastq_file_path: Path = add_flow_cell_name_to_fastq_file_path(
        fastq_file_path=demultiplex_fastq_file_path, flow_cell_name=bcl2fastq_flow_cell_id
    )

    # THEN the fastq file path should be returned equal to the original fastq file path
    assert renamed_fastq_file_path == demultiplex_fastq_file_path


def test_get_undetermined_fastqs_no_matching_files(tmp_path):
    # GIVEN a lane and a flow cell with no undetermined fastq files

    # WHEN reetrieving undetermined fastqs for the lane
    result = get_undetermined_fastqs(lane=1, flow_cell_path=tmp_path)

    # THEN no undetermined fastq files should be returned
    assert not result


def test_get_undetermined_fastqs_single_matching_file(tmp_path):
    # GIVEN a flow cell with one undetermined fastq file
    expected_file: Path = Path(tmp_path, "Undetermined_L001_R1.fastq.gz")
    expected_file.touch()

    # WHEN retrieving undetermined fastqs for the lane
    result = get_undetermined_fastqs(lane=1, flow_cell_path=tmp_path)

    # THEN the undetermined fastq file for the lane should be returned
    assert result == [expected_file]


def test_get_undetermined_fastqs_multiple_matching_files(tmp_path):
    # GIVEN a flow cell with multiple undetermined fastq files for a lane
    expected_files = [
        Path(tmp_path, "Undetermined_L001_R1.fastq.gz"),
        Path(tmp_path, "Undetermined_L001_R2.fastq.gz"),
    ]
    for file in expected_files:
        file.touch()

    # WHEN retrieving the undetermined fastqs for the lane
    result = get_undetermined_fastqs(lane=1, flow_cell_path=tmp_path)

    # THEN the undetermined fastq files for the lane should be returned
    assert set(result) == set(expected_files)
