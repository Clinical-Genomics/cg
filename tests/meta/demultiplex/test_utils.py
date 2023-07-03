from pathlib import Path

from cg.constants.constants import FileExtensions
from cg.meta.demultiplex.utils import (
    get_lane_from_sample_fastq,
    get_sample_fastq_paths_from_flow_cell,
    get_sample_id_from_sample_fastq,
)


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
    result = get_sample_fastq_paths_from_flow_cell(
        flow_cell_directory=flow_cell_dir
    )

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
    result = get_sample_fastq_paths_from_flow_cell(
        flow_cell_directory=flow_cell_dir
    )

    # THEN we should not get any files
    assert len(result) == 0
    assert invalid_fastq_file not in result
