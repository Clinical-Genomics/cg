from pathlib import Path

from cg.constants.constants import FileExtensions
from cg.meta.demultiplex.utils import (
    get_lane_from_sample_fastq,
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
