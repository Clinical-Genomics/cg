from pathlib import Path
from cg.services.fastq_concatenation_service.fastq_concatenation_service import (
    FastqConcatenationService,
)


def test_empty_directory(fastq_file_service: FastqConcatenationService, tmp_path):
    # GIVEN an empty directory

    # GIVEN output files
    forward_output_path = Path(tmp_path, "forward.fastq.gz")
    reverse_output_path = Path(tmp_path, "reverse.fastq.gz")

    # WHEN concatenating the reads
    fastq_file_service.concatenate(
        fastq_directory=tmp_path,
        forward_output_path=forward_output_path,
        reverse_output_path=reverse_output_path,
    )

    # THEN the output files should not exist
    assert not forward_output_path.exists()
    assert not reverse_output_path.exists()


def test_concatenate(fastq_file_service: FastqConcatenationService, fastqs_dir: Path):
    # GIVEN a directory with forward and reverse reads

    # GIVEN output files for the concatenated reads
    forward_output_path = Path(fastqs_dir, "forward.fastq.gz")
    reverse_output_path = Path(fastqs_dir, "reverse.fastq.gz")

    # WHEN concatenating the reads
    fastq_file_service.concatenate(
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
    fastq_file_service: FastqConcatenationService, fastqs_dir: Path
):
    # GIVEN a directory with forward and reverse reads
    existing_fastq_files = list(fastqs_dir.iterdir())
    existing_forward: Path = existing_fastq_files[0]

    # GIVEN that the forward output file already exists
    forward_output_path = existing_forward
    reverse_output_path = Path(fastqs_dir, "reverse.fastq.gz")

    # WHEN concatenating the reads
    fastq_file_service.concatenate(
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


def test_concatenate_missing_reverse(
    fastq_file_service: FastqConcatenationService, fastqs_forward: Path, tmp_path
):
    # GIVEN a directory with forward reads only

    # GIVEN output files for the concatenated reads
    forward_output_path = Path(tmp_path, "forward.fastq.gz")
    reverse_output_path = Path(tmp_path, "reverse.fastq.gz")

    # WHEN concatenating the reads
    fastq_file_service.concatenate(
        fastq_directory=fastqs_forward,
        forward_output_path=forward_output_path,
        reverse_output_path=reverse_output_path,
    )

    # THEN forward reads should be concatenated
    assert forward_output_path.exists()

    # THEN reverse reads should not exist
    assert not reverse_output_path.exists()
