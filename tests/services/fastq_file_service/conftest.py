from pathlib import Path

import pytest

from cg.services.fastq_file_service.fastq_file_service import FastqFileService


@pytest.fixture
def fastq_file_service():
    return FastqFileService()


def create_fastqs_directory(
    sample_name: str, number_forward_reads: int, number_reverse_reads: int, tmp_path: Path
) -> Path:
    fastq_dir = Path(tmp_path, "fastqs")
    fastq_dir.mkdir()
    for i in range(number_forward_reads):
        file = Path(fastq_dir, f"{sample_name}_R1_{i}.fastq.gz")
        file.write_text(f"forward read {i}")

    for i in range(number_reverse_reads):
        file = Path(fastq_dir, f"{sample_name}_R2_{i}.fastq.gz")
        file.write_text(f"reverse read {i}")
    return fastq_dir


@pytest.fixture
def fastqs_dir(tmp_path: Path, sample_name: str) -> Path:
    return create_fastqs_directory(
        sample_name=sample_name, number_forward_reads=3, number_reverse_reads=3, tmp_path=tmp_path
    )


@pytest.fixture
def fastqs_forward(tmp_path, sample_name: str) -> Path:
    """Return a directory with only forward reads."""
    return create_fastqs_directory(
        sample_name=sample_name, number_forward_reads=3, number_reverse_reads=0, tmp_path=tmp_path
    )


@pytest.fixture
def concatenated_fastqs_dir(fastqs_dir: Path, sample_name: str) -> Path:
    """Return a directory with concatenated fastq files."""
    for i in [1, 2]:
        file = Path(fastqs_dir, f"{sample_name}_R{i}.fastq.gz")
        file.write_text(f"Concatenated read {i}")
    return fastqs_dir
