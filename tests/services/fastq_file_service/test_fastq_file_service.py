from pathlib import Path

import pytest
from cg.constants.constants import ReadDirection

from cg.services.fastq_concatenation_service.fastq_concatenation_service import (
    FastqConcatenationService,
)
from cg.services.fastq_concatenation_service.utils import generate_concatenated_fastq_delivery_path


def test_empty_directory(
    fastq_file_service: FastqConcatenationService, tmp_path: Path, sample_id: str
):
    # GIVEN an empty directory

    # GIVEN output files
    forward_output_path = Path(tmp_path, "forward.fastq.gz")
    reverse_output_path = Path(tmp_path, "reverse.fastq.gz")

    # WHEN concatenating the reads
    fastq_file_service.concatenate(
        sample_id=sample_id,
        fastq_directory=tmp_path,
        forward_output_path=forward_output_path,
        reverse_output_path=reverse_output_path,
    )

    # THEN the output files should not exist
    assert not forward_output_path.exists()
    assert not reverse_output_path.exists()


def test_concatenate(
    fastq_file_service: FastqConcatenationService, fastqs_dir: Path, sample_id: str
):
    # GIVEN a directory with forward and reverse reads

    # GIVEN output files for the concatenated reads
    forward_output_path = Path(fastqs_dir, "forward.fastq.gz")
    reverse_output_path = Path(fastqs_dir, "reverse.fastq.gz")

    # WHEN concatenating the reads
    fastq_file_service.concatenate(
        sample_id=sample_id,
        fastq_directory=fastqs_dir,
        forward_output_path=forward_output_path,
        reverse_output_path=reverse_output_path,
        remove_raw=True,
    )

    # THEN the output files should exist
    assert forward_output_path.exists()
    assert reverse_output_path.exists()

    # THEN the concatenated forward reads only contain forward reads
    assert "forward" in forward_output_path.read_text()
    assert "reverse" not in forward_output_path.read_text()

    # THEN the concatenated reverse reads only contain reverse reads
    assert "reverse" in reverse_output_path.read_text()
    assert "forward" not in reverse_output_path.read_text()


def test_concatenate_when_output_exists(
    fastq_file_service: FastqConcatenationService,
    fastq_dir_existing_concatenated_files: Path,
    sample_id: str,
):
    """Test that existing concatenated files are overwritten when already existing."""
    # GIVEN a directory with forward and reverse reads
    forward_output_path = Path(fastq_dir_existing_concatenated_files, "forward.fastq.gz")
    reverse_output_path = Path(fastq_dir_existing_concatenated_files, "reverse.fastq.gz")

    # GIVEN that the forward output file already exists
    assert forward_output_path.exists()
    assert reverse_output_path.exists()
    assert "Existing" in forward_output_path.read_text()
    assert "Existing" in reverse_output_path.read_text()

    # WHEN concatenating the reads
    fastq_file_service.concatenate(
        sample_id=sample_id,
        fastq_directory=fastq_dir_existing_concatenated_files,
        forward_output_path=forward_output_path,
        reverse_output_path=reverse_output_path,
        remove_raw=True,
    )

    # THEN the output files should exist
    assert forward_output_path.exists()
    assert reverse_output_path.exists()

    # THEN the concatenated forward reads only contain forward reads
    assert "forward" in forward_output_path.read_text()
    assert "reverse" not in forward_output_path.read_text()
    assert "Existing" not in forward_output_path.read_text()

    # THEN the concatenated reverse reads only contain reverse reads
    assert "reverse" in reverse_output_path.read_text()
    assert "forward" not in reverse_output_path.read_text()
    assert "Existing" not in reverse_output_path.read_text()


def test_concatenate_missing_reverse(
    fastq_file_service: FastqConcatenationService, fastqs_forward: Path, tmp_path, sample_id: str
):
    # GIVEN a directory with forward reads only

    # GIVEN output files for the concatenated reads
    forward_output_path = Path(tmp_path, "forward.fastq.gz")
    reverse_output_path = Path(tmp_path, "reverse.fastq.gz")

    # WHEN concatenating the reads
    fastq_file_service.concatenate(
        sample_id=sample_id,
        fastq_directory=fastqs_forward,
        forward_output_path=forward_output_path,
        reverse_output_path=reverse_output_path,
    )

    # THEN forward reads should be concatenated
    assert forward_output_path.exists()

    # THEN reverse reads should not exist
    assert not reverse_output_path.exists()


def test_concatenate_fastqs_multiple_samples_in_dir(
    fastqs_multiple_samples: Path,
    fastq_file_service: FastqConcatenationService,
    sample_id: str,
    another_sample_id: str,
    tmp_path: Path,
):
    # GIVEN a fastq directory with fastq files for multiple samples that should be concatenated
    samples: list[str] = [sample_id, another_sample_id]

    # GIVEN output files for the concatenated reads
    for fastq_sample in samples:
        forward_output_path = Path(tmp_path, f"{fastq_sample}_forward.fastq.gz")
        reverse_output_path = Path(tmp_path, f"{fastq_sample}_reverse.fastq.gz")

        # WHEN concatenating the reads
        fastq_file_service.concatenate(
            sample_id=fastq_sample,
            fastq_directory=fastqs_multiple_samples,
            forward_output_path=forward_output_path,
            reverse_output_path=reverse_output_path,
            remove_raw=True,
        )

        not_current_sample: str = another_sample_id if fastq_sample == sample_id else sample_id
        # THEN the output files should exist
        assert forward_output_path.exists()
        assert reverse_output_path.exists()

        # THEN the concatenated forward reads only contain forward reads
        assert "forward" in forward_output_path.read_text()
        assert "reverse" not in forward_output_path.read_text()
        assert fastq_sample in forward_output_path.read_text()
        assert not_current_sample not in forward_output_path.read_text()

        # THEN the concatenated reverse reads only contain reverse reads
        assert "reverse" in reverse_output_path.read_text()
        assert "forward" not in reverse_output_path.read_text()
        assert fastq_sample in reverse_output_path.read_text()
        assert not_current_sample not in reverse_output_path.read_text()


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
    # GIVEN a fastq direcrory, a sample name and a read direction

    # WHEN generating the concatenated fastq delivery path

    # THEN the output path should be as expected
    assert (
        generate_concatenated_fastq_delivery_path(
            fastq_directory=fastq_directory, sample_name=sample_name, direction=direction
        )
        == expected_output_path
    )
