from pathlib import Path

import pytest

from cg.constants.constants import FileExtensions
from cg.constants.demultiplexing import BclConverter, DemultiplexingDirsAndFiles
from cg.constants.sequencing import FLOWCELL_Q30_THRESHOLD, Sequencers
from cg.meta.demultiplex.utils import (
    create_delivery_file_in_flow_cell_directory,
    get_bcl_converter_name,
    get_lane_from_sample_fastq,
    get_q30_threshold,
    get_sample_fastq_paths_from_flow_cell,
    get_sample_id_from_sample_fastq,
    get_sample_sheet_path,
)
from cg.meta.demultiplex.validation import is_bcl2fastq_demux_folder_structure


def test_get_sample_id_from_sample_fastq_file():
    # GIVEN a sample fastq path
    sample_id = "ACC12164A17"
    sample_fastq = Path(f"Sample_{sample_id}/xxx{FileExtensions.FASTQ}{FileExtensions.GZIP}")

    # WHEN we get sample id from the sample fastq
    result = get_sample_id_from_sample_fastq(sample_fastq)

    # THEN we should get the correct sample id
    assert result == sample_id


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


def test_get_valid_flowcell_sample_fastq_file_path(tmpdir_factory):
    # GIVEN a flow cell directory
    flow_cell_dir = Path(tmpdir_factory.mktemp("flow_cell"))

    # GIVEN some files in temporary directory
    sample_dir = flow_cell_dir / "Unaligned" / "Project_sample" / "Sample_test"
    sample_dir.mkdir(parents=True)
    valid_sample_fastq_directory_1 = Path(
        sample_dir, f"Sample_ABC{FileExtensions.FASTQ}{FileExtensions.GZIP}"
    )
    valid_sample_fastq_directory_2 = Path(
        sample_dir, f"Sample_ABC_123{FileExtensions.FASTQ}{FileExtensions.GZIP}"
    )
    valid_sample_fastq_directory_1.touch()
    valid_sample_fastq_directory_2.touch()

    # WHEN we get flowcell sample fastq file paths
    result = get_sample_fastq_paths_from_flow_cell(flow_cell_directory=flow_cell_dir)

    # THEN we should only get the valid files
    assert len(result) == 2
    assert valid_sample_fastq_directory_1 in result


def test_get_invalid_flowcell_sample_fastq_file_path(tmpdir_factory):
    # GIVEN a DemuxPostProcessing API

    # GIVEN a flow cell directory
    flow_cell_dir = Path(tmpdir_factory.mktemp("flow_cell"))

    # GIVEN some files in temporary directory
    project_dir = Path(flow_cell_dir, "Unaligned", "Project_sample")
    project_dir.mkdir(parents=True)
    invalid_fastq_file = Path(project_dir, f"file{FileExtensions.FASTQ}{FileExtensions.GZIP}")
    invalid_fastq_file.touch()

    # WHEN we get flowcell sample fastq file paths
    result = get_sample_fastq_paths_from_flow_cell(flow_cell_directory=flow_cell_dir)

    # THEN we should not get any files
    assert len(result) == 0
    assert invalid_fastq_file not in result


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


def test_create_delivery_file_in_flow_cell_directory(tmp_path: Path):
    # GIVEN a temporary directory as the flow cell directory
    flow_cell_directory = tmp_path

    # WHEN the create_delivery_file_in_flow_cell_directory function is called
    create_delivery_file_in_flow_cell_directory(flow_cell_directory)

    # THEN a delivery file should exist in the flow cell directory
    assert (flow_cell_directory / DemultiplexingDirsAndFiles.DELIVERY).exists()


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
