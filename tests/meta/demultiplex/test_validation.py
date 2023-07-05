from pathlib import Path

import pytest
from cg.constants.constants import FileExtensions
from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.exc import FlowCellError
from cg.meta.demultiplex.utils import create_delivery_file_in_flow_cell_directory
from cg.meta.demultiplex.validation import (
    is_file_path_compressed_fastq,
    is_flow_cell_directory_valid,
    is_lane_in_fastq_file_name,
    is_sample_id_in_directory_name,
    validate_sample_fastq_file,
)


def test_validate_sample_fastq_with_valid_file():
    # GIVEN a sample fastq file with a lane number and sample id in the parent directory name
    sample_fastq = Path("Sample_123/sample_L0002.fastq.gz")

    # WHEN validating the sample fastq file
    validate_sample_fastq_file(sample_fastq)

    # THEN no exception should be raised


def test_validate_sample_fastq_without_sample_id_in_parent_directory_name():
    # GIVEN a sample fastq file without a sample id in the parent directory name
    sample_fastq = Path("sample_L0002.fastq.gz")

    # WHEN validating the sample fastq file
    # THEN a ValueError should be raised
    with pytest.raises(
        ValueError, match="Parent directory name of sample fastq must contain 'Sample_<sample_id>'."
    ):
        validate_sample_fastq_file(sample_fastq)


def test_validate_sample_fastq_without_lane_number():
    # GIVEN a sample fastq file without a lane number
    sample_fastq = Path("Sample_123/sample.fastq.gz")

    # WHEN validating the sample fastq file
    # THEN a ValueError should be raised
    with pytest.raises(
        ValueError, match="Sample fastq must contain lane number formatted as '_L<lane_number>'."
    ):
        validate_sample_fastq_file(sample_fastq)


def test_validate_sample_fastq_without_fastq_file_extension():
    # GIVEN a sample fastq file without a .fastq.gz file extension
    sample_fastq = Path("Sample_123/sample_L0002.fastq")

    # WHEN validating the sample fastq file
    # THEN a ValueError should be raised
    with pytest.raises(
        ValueError, match=f"Sample fastq must end with {FileExtensions.FASTQ}{FileExtensions.GZIP}."
    ):
        validate_sample_fastq_file(sample_fastq)


def test_is_file_path_compressed_fastq_with_valid_file():
    # GIVEN a valid .fastq.gz file
    file_path = Path("sample_L0002.fastq.gz")

    # WHEN checking if the file path is a compressed fastq file
    result = is_file_path_compressed_fastq(file_path)

    # THEN the result should be True
    assert result is True


def test_is_file_path_compressed_fastq_with_invalid_file():
    # GIVEN a file with invalid extension
    file_path = Path("sample_L0002.fastq")

    # WHEN checking if the file path is a compressed fastq file
    result = is_file_path_compressed_fastq(file_path)

    # THEN the result should be False
    assert result is False


def test_is_lane_in_fastq_file_name_with_valid_file():
    # GIVEN a valid file containing lane number
    file_path = Path("sample_L0002.fastq.gz")

    # WHEN checking if the lane number is in the fastq file name
    result = is_lane_in_fastq_file_name(file_path)

    # THEN the result should be True
    assert result is True


def test_is_lane_in_fastq_file_name_with_invalid_file():
    # GIVEN a file without lane number
    file_path = Path("sample.fastq.gz")

    # WHEN checking if the lane number is in the fastq file name
    result = is_lane_in_fastq_file_name(file_path)

    # THEN the result should be False
    assert result is False


def test_is_sample_id_in_directory_name_with_valid_directory():
    # GIVEN a directory containing sample id
    directory = Path("Sample_123")

    # WHEN checking if the sample id is in the directory name
    result = is_sample_id_in_directory_name(directory)

    # THEN the result should be True
    assert result is True


def test_is_sample_id_in_directory_name_with_invalid_directory():
    # GIVEN a directory without sample id
    directory = Path("sample")

    # WHEN checking if the sample id is in the directory name
    result = is_sample_id_in_directory_name(directory)

    # THEN the result should be False
    assert result is False


def test_is_flow_cell_directory_valid_when_directory_exists_and_demultiplexing_complete(
    tmp_path: Path,
):
    # GIVEN a temporary directory as the flow cell directory with a demux complete file
    flow_cell_directory = tmp_path
    Path(flow_cell_directory, DemultiplexingDirsAndFiles.DEMUX_COMPLETE).touch()

    # WHEN validating the flow cell directory
    is_flow_cell_directory_valid(flow_cell_directory)

    # THEN no exception is raised


def test_is_flow_cell_directory_valid_when_directory_exists_but_demultiplexing_not_complete(
    tmp_path: Path,
):
    # GIVEN a temporary directory as the flow cell directory without a demux complete file
    flow_cell_directory = tmp_path

    # WHEN validating the flow cell directory
    with pytest.raises(FlowCellError):
        is_flow_cell_directory_valid(flow_cell_directory)


def test_is_flow_cell_directory_valid_when_directory_does_not_exist():
    # GIVEN a directory that doesn't exist
    flow_cell_directory = Path("non_existent_directory")

    # WHEN validating the flow cell directory
    with pytest.raises(FlowCellError):
        is_flow_cell_directory_valid(flow_cell_directory)
