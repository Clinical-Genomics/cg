from pathlib import Path
import pytest
from cg.meta.deliver.fastq_path_generator import (
    generate_concatenated_fastq_delivery_path,
)
from cg.constants.constants import ReadDirection


@pytest.mark.parametrize(
    "fastq_directory, sample_name, direction, expected_output_path",
    [
        (
            Path("/path/to/fastq_directory"),
            "sample1",
            ReadDirection.FORWARD,
            Path("/path/to/fastq_directory/sample1_1.fastq.gz"),
        ),
        (
            Path("/path/to/fastq_directory"),
            "sample1",
            ReadDirection.REVERSE,
            Path("/path/to/fastq_directory/sample1_2.fastq.gz"),
        ),
    ],
    ids=["forward", "reverse"],
)
def test_generate_concatenated_fastq_delivery_path(
    fastq_directory: Path, sample_name: str, direction: int, expected_output_path: Path
):
    assert (
        generate_concatenated_fastq_delivery_path(
            fastq_directory=fastq_directory, sample_name=sample_name, direction=direction
        )
        == expected_output_path
    )
