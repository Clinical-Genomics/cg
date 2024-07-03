from pathlib import Path

import pytest

from cg.constants import FileExtensions
from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.exc import FlowCellError, MissingFilesError
from cg.services.illumina_services.illumina_post_processing_service.validation import (
    is_demultiplexing_complete,
    is_flow_cell_ready_for_delivery,
    validate_demultiplexing_complete,
    validate_flow_cell_delivery_status,
    validate_flow_cell_has_fastq_files,
    validate_sample_sheet_exists,
)
from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData


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
    assert not result


def test_validate_sample_sheet_exists_raises_error(hiseq_2500_custom_index_flow_cell_dir: Path):
    # GIVEN a flow cell without a sample sheet in housekeeper
    flow_cell = IlluminaRunDirectoryData(sequencing_run_path=hiseq_2500_custom_index_flow_cell_dir)
    flow_cell._sample_sheet_path_hk = None
    # WHEN validating the existence of the sample sheet
    # THEN it should raise a FlowCellError
    with pytest.raises(FlowCellError):
        validate_sample_sheet_exists(flow_cell=flow_cell)


def test_validate_sample_sheet_exists(hiseq_2500_custom_index_flow_cell_dir: Path):
    # GIVEN a path with a sample sheet
    # GIVEN a flow cell without a sample sheet in housekeeper
    flow_cell = IlluminaRunDirectoryData(sequencing_run_path=hiseq_2500_custom_index_flow_cell_dir)
    sample_sheet_path = Path(
        hiseq_2500_custom_index_flow_cell_dir, DemultiplexingDirsAndFiles.SAMPLE_SHEET_FILE_NAME
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
    novaseqx_flow_cell_with_sample_sheet_no_fastq: IlluminaRunDirectoryData,
):
    """Test the check of a flow cells with one sample fastq file does not raise an error."""
    # GIVEN a demultiplexed flow cell with no fastq files and a sample sheet

    # GIVEN that a valid sample fastq file is added to the directory
    sample_id: str = novaseqx_flow_cell_with_sample_sheet_no_fastq.sample_sheet.get_sample_ids()[0]
    fastq_file_path = Path(
        novaseqx_flow_cell_with_sample_sheet_no_fastq.path,
        f"{sample_id}_S11_L1_R1_{FileExtensions.FASTQ}{FileExtensions.GZIP}",
    )
    fastq_file_path.touch()

    # WHEN checking if the flow cell has fastq files for the samples
    validate_flow_cell_has_fastq_files(novaseqx_flow_cell_with_sample_sheet_no_fastq)

    # THEN no error is raised


def test_validate_samples_have_fastq_files_fails(
    novaseqx_flow_cell_with_sample_sheet_no_fastq,
):
    """Test the check of a flow cells with one sample fastq file does not raise an error."""
    # GIVEN a demultiplexed flow cell with no fastq files

    # GIVEN a that the flow cell has a sample sheet in Housekeeper
    assert novaseqx_flow_cell_with_sample_sheet_no_fastq.get_sample_sheet_path_hk()

    # WHEN checking if the flow cell has fastq files for the samples
    with pytest.raises(MissingFilesError):
        # THEN an error is raised
        validate_flow_cell_has_fastq_files(flow_cell=novaseqx_flow_cell_with_sample_sheet_no_fastq)
