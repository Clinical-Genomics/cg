from pathlib import Path
from mock import MagicMock, PropertyMock, patch

import pytest

from cg.constants.constants import FileExtensions
from cg.constants.demultiplexing import BclConverter, DemultiplexingDirsAndFiles
from cg.constants.sequencing import FLOWCELL_Q30_THRESHOLD, Sequencers
from cg.exc import FlowCellError
from cg.meta.demultiplex.utils import (
    create_delivery_file_in_flow_cell_directory,
    get_bcl_converter_name,
    get_lane_from_sample_fastq,
    get_q30_threshold,
    get_sample_internal_ids_from_flow_cell,
    get_sample_sheet_path,
    parse_flow_cell_directory_data,
)
from cg.meta.demultiplex.validation import is_bcl2fastq_demux_folder_structure
from cg.models.demultiplex.flow_cell import FlowCellDirectoryData


def test_get_lane_from_sample_fastq_file_path():
    # GIVEN a sample fastq path
    lane = 4
    sample_fastq_path = Path(
        f"H5CYFDSX7_ACC12164A17_S367_L00{lane}_R1_001{FileExtensions.FASTQ}{FileExtensions.GZIP}",
    )

    # WHEN we get lane from the sample fastq file path
    result = get_lane_from_sample_fastq(sample_fastq_path)

    # THEN we should get the correct lane
    assert result == lane


def test_get_lane_from_sample_fastq_file_path_no_flowcell():
    # GIVEN a sample fastq path without a flow cell id
    lane = 4
    sample_fastq_path = Path(
        f"ACC12164A17_S367_L00{lane}_R1_001{FileExtensions.FASTQ}{FileExtensions.GZIP}",
    )

    # WHEN we get lane from the sample fastq file path
    result = get_lane_from_sample_fastq(sample_fastq_path)

    # THEN we should get the correct lane
    assert result == lane


def test_is_bcl2fastq_folder_structure(bcl2fastq_folder_structure: Path):
    # GIVEN a bcl2fastq folder structure
    # WHEN checking if it is a bcl2fastq folder structure
    is_bcl2fastq_folder_structure = is_bcl2fastq_demux_folder_structure(bcl2fastq_folder_structure)

    # THEN it should be a bcl2fastq folder structure
    assert is_bcl2fastq_folder_structure is True


def test_is_not_bcl2fastq_folder_structure(not_bcl2fastq_folder_structure: Path):
    # GIVEN not folder structure which is not formatted correctly for bcl2fastq

    # WHEN checking if it is a bcl2fastq folder structure
    is_bcl2fastq_folder_structure = is_bcl2fastq_demux_folder_structure(
        not_bcl2fastq_folder_structure
    )

    # THEN it should not be a bcl2fastq folder structure
    assert is_bcl2fastq_folder_structure is False


def test_get_bcl_converter_bcl2fastq(bcl2fastq_folder_structure: Path):
    # GIVEN a bcl2fastq folder structure
    # WHEN getting the bcl converter
    bcl_converter: str = get_bcl_converter_name(bcl2fastq_folder_structure)

    # THEN it should be bcl2fastq
    assert bcl_converter == BclConverter.BCL2FASTQ


def test_get_bcl_converter_bclconvert():
    # GIVEN any folder structure which is not bcl2fastq
    # WHEN getting the bcl converter
    bcl_converter: str = get_bcl_converter_name(Path())

    # THEN it returns bclconvert
    assert bcl_converter == BclConverter.BCLCONVERT


def test_validate_demux_complete_flow_cell_directory_when_it_exists(tmp_path: Path):
    # GIVEN a temporary directory as the flow cell directory with a demux complete file
    flow_cell_directory = tmp_path
    Path(flow_cell_directory, DemultiplexingDirsAndFiles.DEMUX_COMPLETE).touch()

    # WHEN the create_delivery_file_in_flow_cell_directory function is called
    create_delivery_file_in_flow_cell_directory(flow_cell_directory)

    # THEN a delivery file should exist in the flow cell directory
    assert (flow_cell_directory / DemultiplexingDirsAndFiles.DEMUX_COMPLETE).exists()


def test_validate_demux_complete_flow_cell_directory_when_it_does_not_exist(tmp_path: Path):
    # GIVEN a temporary directory as the flow cell directory without a demux complete file
    flow_cell_directory = tmp_path

    # WHEN the create_delivery_file_in_flow_cell_directory function is called
    create_delivery_file_in_flow_cell_directory(flow_cell_directory)

    # THEN a delivery file should not exist in the flow cell directory
    assert not (flow_cell_directory / DemultiplexingDirsAndFiles.DEMUX_COMPLETE).exists()


def test_get_q30_threshold():
    # GIVEN a specific sequencer type
    sequencer_type = Sequencers.HISEQGA

    # WHEN getting the Q30 threshold for the sequencer type
    q30_threshold = get_q30_threshold(sequencer_type)

    # THEN the correct Q30 threshold should be returned
    assert q30_threshold == FLOWCELL_Q30_THRESHOLD[sequencer_type]


def test_get_sample_sheet_path_found(tmp_path: Path):
    # GIVEN a temporary directory as the flow cell directory
    flow_cell_directory = tmp_path

    # GIVEN a sample sheet file in the flow cell directory
    sample_sheet_path = Path(flow_cell_directory, DemultiplexingDirsAndFiles.SAMPLE_SHEET_FILE_NAME)
    sample_sheet_path.touch()

    # WHEN the sample sheet is retrieved
    found_sample_sheet_path = get_sample_sheet_path(flow_cell_directory)

    # THEN the path to the sample sheet file should be returned
    assert found_sample_sheet_path == sample_sheet_path


def test_get_sample_sheet_path_found_in_nested_directory(tmp_path: Path):
    # GIVEN a temporary directory as the flow cell directory
    flow_cell_directory = tmp_path

    # GIVEN a nested directory within the flow cell directory
    nested_directory = Path(flow_cell_directory, "nested")
    nested_directory.mkdir()

    # GIVEN a sample sheet file in the nested directory
    sample_sheet_path = Path(nested_directory, DemultiplexingDirsAndFiles.SAMPLE_SHEET_FILE_NAME)
    sample_sheet_path.touch()

    # WHEN the sample sheet is retrieved
    found_sample_sheet_path = get_sample_sheet_path(flow_cell_directory)

    # THEN the path to the sample sheet file should be returned
    assert found_sample_sheet_path == sample_sheet_path


def test_get_sample_sheet_path_not_found(tmp_path: Path):
    # GIVEN a temporary directory as the flow cell directory without a sample sheet file
    flow_cell_directory = tmp_path

    # WHEN the sample sheet is retrieved
    # THEN a FileNotFoundError should be raised
    with pytest.raises(FileNotFoundError):
        get_sample_sheet_path(flow_cell_directory)


def test_get_sample_ids_from_sample_sheet():
    # GIVEN some flow cell samples
    mock_sample1 = MagicMock()
    mock_sample1.sample_id = "sample1_index1"
    mock_sample2 = MagicMock()
    mock_sample2.sample_id = "sample2_index2"
    mock_samples = [mock_sample1, mock_sample2]

    # GIVEN a sample sheet with the samples
    mock_sample_sheet = MagicMock()
    type(mock_sample_sheet).samples = PropertyMock(return_value=mock_samples)

    # GIVEN a flow cell data with the parsed sample sheet object
    mock_flow_cell_data = MagicMock()
    mock_flow_cell_data.get_sample_sheet.return_value = mock_sample_sheet

    # WHEN extracting the sample ids from the sample sheet in the flow cell directory data
    result = get_sample_internal_ids_from_flow_cell(mock_flow_cell_data)

    # THEN the sample ids are returned without the index
    assert result == ["sample1", "sample2"]


@patch("cg.meta.demultiplex.utils.is_flow_cell_directory_valid", return_value=False)
# GIVEN a flow cell directory which is not valid
# WHEN parsing the flow cell directory data
# THEN a FlowCellError should be raised
def test_parse_flow_cell_directory_data_invalid(mocked_function):
    with pytest.raises(FlowCellError):
        parse_flow_cell_directory_data(Path("dummy_path"), "dummy_bcl_converter")


@patch("cg.meta.demultiplex.utils.is_flow_cell_directory_valid", return_value=True)
def test_parse_flow_cell_directory_data_valid(mocked_function):
    # GIVEN a flow cell directory which is valid
    # WHEN parsing the flow cell directory data
    flow_cell_run_directory = "20230508_LH00188_0003_A22522YLT3"
    result = parse_flow_cell_directory_data(Path(flow_cell_run_directory), "dummy_bcl_converter")

    # THEN a FlowCellDirectoryData object should be returned
    assert isinstance(result, FlowCellDirectoryData)

    # THEN the flow cell path and bcl converter should be set
    assert result.path == Path(flow_cell_run_directory)
    assert result.bcl_converter == "dummy_bcl_converter"
