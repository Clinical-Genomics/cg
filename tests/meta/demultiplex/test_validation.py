from pathlib import Path

import pytest

from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.exc import FlowCellError

from cg.meta.demultiplex.validation import (
    is_demultiplexing_complete,
    is_file_path_compressed_fastq,
    is_flow_cell_ready_for_delivery,
    is_lane_in_fastq_file_name,
    is_sample_id_in_directory_name,
    is_valid_sample_fastq_file,
    validate_demultiplexing_complete,
    validate_flow_cell_delivery_status,
    validate_sample_sheet_exists,
)
from cg.models.demultiplex.flow_cell import FlowCellDirectoryData


def test_validate_sample_fastq_with_valid_file():
    # GIVEN a sample fastq file with a lane number and sample id in the parent directory name
    sample_fastq = Path("Sample_123/sample_L0002.fastq.gz")

    # WHEN validating the sample fastq file
    is_valid = is_valid_sample_fastq_file(sample_fastq=sample_fastq, sample_internal_id="sample")

    # THEN it should be valid
    assert is_valid


def test_validate_sample_fastq_without_sample_id_in_parent_directory_name():
    # GIVEN a sample fastq file without a sample id in the parent directory name or file name
    sample_fastq = Path("L0002.fastq.gz")

    # WHEN validating the sample fastq file
    is_valid_fastq = is_valid_sample_fastq_file(
        sample_fastq=sample_fastq, sample_internal_id="sample_id"
    )

    # THEN it should not be valid
    assert not is_valid_fastq


def test_validate_sample_fastq_without_lane_number_in_path():
    # GIVEN a sample fastq file without a lane number
    sample_fastq = Path("Sample_123/sample_id.fastq.gz")

    # WHEN validating the sample fastq file
    is_valid_fastq = is_valid_sample_fastq_file(sample_fastq, sample_internal_id="sample_id")

    # THEN it should not be valid
    assert not is_valid_fastq


def test_validate_sample_fastq_with_invalid_file_extension():
    # GIVEN a sample fastq file without a valid file extension
    sample_fastq = Path("Sample_123/123_L0002.fastq")

    # WHEN validating the sample fastq file
    is_valid_fastq = is_valid_sample_fastq_file(sample_fastq, sample_internal_id="123")

    # THEN it should not be valid
    assert not is_valid_fastq


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
    result = is_sample_id_in_directory_name(directory=directory, sample_internal_id="123")

    # THEN the result should be True
    assert result is True


def test_is_sample_id_in_directory_name_with_invalid_directory():
    # GIVEN a directory without sample id
    directory = Path("sample/123_L0002.fastq.gz")

    # WHEN checking if the sample id is in the directory name
    result = is_sample_id_in_directory_name(directory=directory, sample_internal_id="sample_id")

    # THEN the result should be False
    assert result is False


def test_is_demultiplexing_complete_true(tmp_path: Path):
    # GIVEN a path where DEMUX_COMPLETE file is present
    (tmp_path / DemultiplexingDirsAndFiles.DEMUX_COMPLETE).touch()

    # WHEN checking if demultiplexing is complete
    result = is_demultiplexing_complete(tmp_path)

    # THEN the result should be True
    assert result == True


def test_is_demultiplexing_complete_false(tmp_path: Path):
    # GIVEN a path without DEMUX_COMPLETE file

    # WHEN checking if demultiplexing is complete
    result = is_demultiplexing_complete(tmp_path)

    # THEN the result should be False
    assert result == False


def test_is_flow_cell_ready_for_delivery_true(tmp_path: Path):
    # GIVEN a path where DELIVERY file is present
    (tmp_path / DemultiplexingDirsAndFiles.DELIVERY).touch()

    # WHEN checking if the flow cell is ready for delivery
    result = is_flow_cell_ready_for_delivery(tmp_path)

    # THEN the result should be True
    assert result == True


def test_is_flow_cell_ready_for_delivery_false(tmp_path: Path):
    # GIVEN a path without DELIVERY file

    # WHEN checking if the flow cell is ready for delivery
    result = is_flow_cell_ready_for_delivery(tmp_path)

    # THEN the result should be False
    assert result == False


def test_validate_sample_sheet_exists_raises_error(bcl2fastq_flow_cell_dir: Path):
    # GIVEN a flow cell without a sample sheet in housekeeper
    flow_cell = FlowCellDirectoryData(flow_cell_path=bcl2fastq_flow_cell_dir)
    flow_cell._sample_sheet_path_hk = None
    # WHEN validating the existence of the sample sheet
    # THEN it should raise a FlowCellError
    with pytest.raises(FlowCellError):
        validate_sample_sheet_exists(flow_cell=flow_cell)


def test_validate_sample_sheet_exists(bcl2fastq_flow_cell_dir: Path):
    # GIVEN a path with a sample sheet
    # GIVEN a flow cell without a sample sheet in housekeeper
    flow_cell = FlowCellDirectoryData(flow_cell_path=bcl2fastq_flow_cell_dir)
    sample_sheet_path = Path(
        bcl2fastq_flow_cell_dir, DemultiplexingDirsAndFiles.SAMPLE_SHEET_FILE_NAME
    )
    sample_sheet_path.touch()
    flow_cell._sample_sheet_path_hk = sample_sheet_path

    # WHEN validating the existence of the sample sheet
    # THEN it should not raise an error
    assert validate_sample_sheet_exists(flow_cell=flow_cell) is None


def test_validate_demultiplexing_complete_raises_error(tmp_path: Path):
    # GIVEN a path without DEMUX_COMPLETE file

    # WHEN validating if demultiplexing is complete
    # THEN it should raise a FlowCellError
    with pytest.raises(FlowCellError):
        validate_demultiplexing_complete(tmp_path)


def test_validate_demultiplexing_complete_no_error(tmp_path: Path):
    # GIVEN a path where DEMUX_COMPLETE file is present
    (tmp_path / DemultiplexingDirsAndFiles.DEMUX_COMPLETE).touch()

    # WHEN validating if demultiplexing is complete
    # THEN it should not raise an error
    assert validate_demultiplexing_complete(tmp_path) is None


def test_validate_flow_cell_delivery_status_no_error(tmp_path: Path):
    # GIVEN a path without DELIVERY file

    # WHEN validating the flow cell delivery status
    # THEN it should not raise an error
    assert (
        validate_flow_cell_delivery_status(flow_cell_output_directory=tmp_path, force=False) is None
    )


def test_validate_flow_cell_delivery_status_raises_error(tmp_path: Path):
    # GIVEN a path where DELIVERY file is present
    (tmp_path / DemultiplexingDirsAndFiles.DELIVERY).touch()

    # WHEN validating the flow cell delivery status
    # THEN it should raise a FlowCellError
    with pytest.raises(FlowCellError):
        validate_flow_cell_delivery_status(flow_cell_output_directory=tmp_path, force=False)


def test_validate_flow_cell_delivery_status_forced(tmp_path: Path):
    # GIVEN a path where DELIVERY file is present
    (tmp_path / DemultiplexingDirsAndFiles.DELIVERY).touch()

    # WHEN validating the flow cell delivery status
    # THEN it should not raise a FlowCellError
    assert (
        validate_flow_cell_delivery_status(flow_cell_output_directory=tmp_path, force=True) is None
    )
