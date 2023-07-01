from pathlib import Path

from cg.constants.constants import FileExtensions
from cg.meta.demultiplex.utils import (
    get_flow_cell_name_from_sample_fastq,
    get_lane_from_sample_fastq,
    get_sample_id_from_sample_fastq,
)


def test_get_flow_cell_from_sample_fastq_file_path():
    # GIVEN a sample fastq path
    flow_cell = "H5CYFDSX7"
    sample_fastq_path = Path(
        f"{flow_cell}_ACC12164A17_S367_L004_R1_001{FileExtensions.FASTQ}{FileExtensions.GZIP}",
    )

    # WHEN we get the flow cell id from sample fastq file path
    result = get_flow_cell_name_from_sample_fastq(sample_fastq_path)

    # THEN we should get the correct flow cell id
    assert result == flow_cell


def test_get_sample_id_from_sample_fastq_file_path():
    # GIVEN a sample fastq path
    sample_id = "ACC12164A17"
    sample_fastq_path = Path(
        f"H5CYFDSX7_{sample_id}_S367_L004_R1_001{FileExtensions.FASTQ}{FileExtensions.GZIP}",
    )

    # WHEN we get sample id from sample fastq file path
    result = get_sample_id_from_sample_fastq(sample_fastq_path)

    # THEN we should get the correct sample id
    assert result == sample_id


def test_get_lane_from_sample_fastq_file_path():
    # GIVEN a sample fastq path
    lane = 4
    sample_fastq_path = Path(
        f"H5CYFDSX7_ACC12164A17_S367_L00{lane}_R1_001{FileExtensions.FASTQ}{FileExtensions.GZIP}",
    )

    # WHEN we get sample id from sample fastq file path
    result = get_lane_from_sample_fastq(sample_fastq_path)

    # THEN we should get the correct sample id
    assert result == lane
