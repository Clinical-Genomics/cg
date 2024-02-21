from pathlib import Path

from cg.services.fastq_file_service.fastq_file_service import FastqFileService


def test_empty_directory(fastq_file_service: FastqFileService, tmp_path):
    # GIVEN an empty directory

    # GIVEN output files
    forward_output = Path(tmp_path, "forward.fastq.gz")
    reverse_output = Path(tmp_path, "reverse.fastq.gz")

    # WHEN concatenating the reads
    fastq_file_service.concatenate(
        fastq_directory=tmp_path,
        forward_output=forward_output,
        reverse_output=reverse_output,
    )

    # THEN the output files should not exist
    assert not forward_output.exists()
    assert not reverse_output.exists()


def test_concatenate(fastq_file_service: FastqFileService, fastqs_dir: Path):
    # GIVEN a directory with forward and reverse reads
    existing_fastq_files = list(fastqs_dir.iterdir())
    existing_forward: Path = existing_fastq_files[0]
    existing_reverse: Path = existing_fastq_files[1]

    existing_forward.write_text("unique forward read")
    existing_reverse.write_text("unique reverse read")

    # GIVEN output files for the concatenated reads
    concatenated_forward = Path(fastqs_dir, "forward.fastq.gz")
    concatenated_reverse = Path(fastqs_dir, "reverse.fastq.gz")

    # WHEN concatenating the reads
    fastq_file_service.concatenate(
        fastq_directory=fastqs_dir,
        forward_output=concatenated_forward,
        reverse_output=concatenated_reverse,
        remove_raw=True,
    )

    # THEN the output files should exist
    assert concatenated_forward.exists()
    assert concatenated_reverse.exists()

    # THEN the output files should contain the concatenated reads
    assert "unique forward read" in concatenated_forward.read_text()
    assert "unique reverse read" in concatenated_reverse.read_text()


def test_concatenate_when_output_exists(fastq_file_service: FastqFileService, fastqs_dir: Path):
    # GIVEN a directory with forward and reverse reads
    existing_fastq_files = list(fastqs_dir.iterdir())
    existing_forward: Path = existing_fastq_files[0]
    existing_reverse: Path = existing_fastq_files[1]

    existing_forward.write_text("unique forward read")
    existing_reverse.write_text("unique reverse read")

    # GIVEN output files for the concatenated reads that already exist
    forward_output = existing_forward
    reverse_output = existing_reverse

    # WHEN concatenating the reads
    fastq_file_service.concatenate(
        fastq_directory=fastqs_dir,
        forward_output=forward_output,
        reverse_output=reverse_output,
        remove_raw=True,
    )

    # THEN the output files should exist
    assert forward_output.exists()
    assert reverse_output.exists()

    # THEN the output files should contain the concatenated reads
    assert "unique forward read" in forward_output.read_text()
    assert "unique reverse read" in reverse_output.read_text()


def test_concatenate_missing_reverse(
    fastq_file_service: FastqFileService, fastqs_forward: Path, tmp_path
):
    # GIVEN a directory with forward reads only

    # GIVEN output files for the concatenated reads
    concatenated_forward = Path(tmp_path, "forward.fastq.gz")
    concatenated_reverse = Path(tmp_path, "reverse.fastq.gz")

    # WHEN concatenating the reads
    fastq_file_service.concatenate(
        fastq_directory=fastqs_forward,
        forward_output=concatenated_forward,
        reverse_output=concatenated_reverse,
    )

    # THEN forward reads should be concatenated
    assert concatenated_forward.exists()

    # THEN reverse reads should not exist
    assert not concatenated_reverse.exists()
