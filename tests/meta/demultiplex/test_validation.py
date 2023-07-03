from pathlib import Path

import pytest
from cg.meta.demultiplex.validation import validate_sample_fastq_file


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
    with pytest.raises(ValueError, match="Directory name must contain 'Sample_<sample_id>'."):
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
    with pytest.raises(ValueError, match="Sample fastq must end with '.fastq.gz'."):
        validate_sample_fastq_file(sample_fastq)
