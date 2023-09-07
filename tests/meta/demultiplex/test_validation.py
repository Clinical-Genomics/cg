from pathlib import Path

import pytest
from cg.apps.demultiplex.sample_sheet.read_sample_sheet import (
    get_sample_internal_ids_from_sample_sheet,
)
from cg.constants import FileExtensions
from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.exc import FlowCellError, MissingFilesError
from cg.meta.demultiplex.validation import (
    is_demultiplexing_complete,
    is_flow_cell_ready_for_delivery,
    validate_demultiplexing_complete,
    validate_flow_cell_delivery_status,
    validate_flow_cell_has_sample_files,
    validate_sample_sheet_exists,
)
from cg.models.demultiplex.flow_cell import FlowCellDirectoryData


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


def test_validate_samples_have_fastq_files_passes(
    mocker, novaseqx_flow_cell_directory: Path, novaseqx_demultiplexed_flow_cell: Path
):
    """Test the check of a flow cells with one sample fastq file does not raise an error."""
    # GIVEN a demultiplexed flow cell with no fastq files
    novaseqx_flow_cell_directory.mkdir(parents=True, exist_ok=True)
    flow_cell_without_fastq = FlowCellDirectoryData(flow_cell_path=novaseqx_flow_cell_directory)

    # GIVEN a that the flow cell has a sample sheet in Housekeeper
    sample_sheet_path = Path(
        novaseqx_demultiplexed_flow_cell, DemultiplexingDirsAndFiles.SAMPLE_SHEET_FILE_NAME
    )
    mocker.patch.object(
        flow_cell_without_fastq, "get_sample_sheet_path_hk", return_value=sample_sheet_path
    )
    assert flow_cell_without_fastq.get_sample_sheet_path_hk()

    # WHEN creating a sample fastq file to the directory
    sample_id: str = get_sample_internal_ids_from_sample_sheet(
        sample_sheet_path=sample_sheet_path,
        flow_cell_sample_type=flow_cell_without_fastq.sample_type,
    )[0]
    fastq_file_path = Path(
        novaseqx_flow_cell_directory,
        f"{sample_id}_S11_L1_R1_{FileExtensions.FASTQ}{FileExtensions.GZIP}",
    )
    fastq_file_path.touch(exist_ok=True)

    # WHEN checking if the flow cell has fastq files for the samples
    validate_flow_cell_has_sample_files(flow_cell=flow_cell_without_fastq)

    # THEN no error is raised


def test_validate_samples_have_fastq_files_fails(
    mocker, novaseqx_flow_cell_directory: Path, novaseqx_demultiplexed_flow_cell: Path
):
    """Test the check of a flow cells with one sample fastq file does not raise an error."""
    # GIVEN a demultiplexed flow cell with no fastq files
    flow_cell_without_fastq = FlowCellDirectoryData(flow_cell_path=novaseqx_flow_cell_directory)

    # GIVEN a that the flow cell has a sample sheet in Housekeeper
    sample_sheet_path = Path(
        novaseqx_demultiplexed_flow_cell, DemultiplexingDirsAndFiles.SAMPLE_SHEET_FILE_NAME
    )
    mocker.patch.object(
        flow_cell_without_fastq, "get_sample_sheet_path_hk", return_value=sample_sheet_path
    )
    assert flow_cell_without_fastq.get_sample_sheet_path_hk()

    # WHEN checking if the flow cell has fastq files for the samples
    with pytest.raises(MissingFilesError):
        # THEN an error is raised
        validate_flow_cell_has_sample_files(flow_cell=flow_cell_without_fastq)
