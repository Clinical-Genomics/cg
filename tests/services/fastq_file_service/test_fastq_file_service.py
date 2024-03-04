from pathlib import Path

from cg.services.fastq_file_service.fastq_file_service import FastqFileService


def test_empty_directory(fastq_file_service: FastqFileService, sample_name: str, tmp_path: Path):
    # GIVEN an empty directory

    # WHEN concatenating the reads
    forward_output, reverse_output = fastq_file_service.concatenate(
        fastq_directory=tmp_path, sample_name=sample_name
    )

    # THEN the output files should not exist
    assert not forward_output
    assert not reverse_output


def test_concatenate(fastq_file_service: FastqFileService, fastqs_dir: Path, sample_name: str):
    # GIVEN a directory with forward and reverse reads

    # WHEN concatenating the reads
    forward_output, reverse_output = fastq_file_service.concatenate(
        fastq_directory=fastqs_dir, sample_name=sample_name, remove_raw=True
    )

    # THEN the output files should exist
    assert forward_output.exists()
    assert reverse_output.exists()

    # THEN the concatenated forward reads only contain forward reads
    assert "forward" in forward_output.read_text()
    assert "reverse" not in forward_output.read_text()

    # THEN the concatenated reverse reads only contain reverse reads
    assert "reverse" in reverse_output.read_text()
    assert "forward" not in reverse_output.read_text()


def test_concatenate_when_output_exists(
    fastq_file_service: FastqFileService, concatenated_fastqs_dir: Path, sample_name: str
):
    # GIVEN a directory with forward and reverse concatenated reads

    # WHEN concatenating the reads
    forward_output, reverse_output = fastq_file_service.concatenate(
        fastq_directory=concatenated_fastqs_dir, sample_name=sample_name, remove_raw=True
    )

    # THEN the output files should exist
    assert forward_output.exists()
    assert reverse_output.exists()

    # THEN the concatenated files only contain their respective reads
    assert "Concatenated read 1" in forward_output.read_text()
    assert "Concatenated read 2" not in forward_output.read_text()


def test_concatenate_missing_reverse(
    fastq_file_service: FastqFileService, fastqs_forward: Path, sample_name: str
):
    # GIVEN a directory with forward reads only

    # WHEN concatenating the reads
    forward_output, reverse_output = fastq_file_service.concatenate(
        fastq_directory=fastqs_forward, sample_name=sample_name
    )

    # THEN forward reads should be concatenated
    assert forward_output and forward_output.exists()

    # THEN reverse reads should not exist
    assert not reverse_output
