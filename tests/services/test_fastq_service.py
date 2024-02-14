from pathlib import Path

from cg.services.fastq_service.fastq_service import FastqService


def test_empty_directory(fastq_service: FastqService, tmp_path):
    # GIVEN an empty directory

    # GIVEN output files
    forward_output = Path(tmp_path, "forward.fastq.gz")
    reverse_output = Path(tmp_path, "reverse.fastq.gz")

    # WHEN concatenating the reads
    fastq_service.concatenate(
        fastq_directory=tmp_path,
        forward_output=forward_output,
        reverse_output=reverse_output,
    )

    # THEN the output files should not exist
    assert not forward_output.exists()
    assert not reverse_output.exists()


def test_concatenate(fastq_service: FastqService, fastqs_dir: Path, tmp_path):
    # GIVEN a directory with forward and reverse reads

    # GIVEN output files for the concatenated reads
    concatenated_forward = Path(tmp_path, "forward.fastq.gz")
    concatenated_reverse = Path(tmp_path, "reverse.fastq.gz")

    # WHEN concatenating the reads
    fastq_service.concatenate(
        fastq_directory=fastqs_dir,
        forward_output=concatenated_forward,
        reverse_output=concatenated_reverse,
    )

    # THEN the output files should exist
    assert concatenated_forward.exists()
    assert concatenated_reverse.exists()

    # THEN the output files should contain the concatenated reads
    assert concatenated_forward.read_text()
    assert concatenated_reverse.read_text()


def test_concatenate_missing_reverse(fastq_service: FastqService, fastqs_forward: Path, tmp_path):
    # GIVEN a directory with forward reads only

    # GIVEN output files for the concatenated reads
    concatenated_forward = Path(tmp_path, "forward.fastq.gz")
    concatenated_reverse = Path(tmp_path, "reverse.fastq.gz")

    # WHEN concatenating the reads
    fastq_service.concatenate(
        fastq_directory=fastqs_forward,
        forward_output=concatenated_forward,
        reverse_output=concatenated_reverse,
    )

    # THEN forward reads should be concatenated
    assert concatenated_forward.exists()

    # THEN reverse reads should not exist
    assert not concatenated_reverse.exists()
