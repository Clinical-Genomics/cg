from pathlib import Path
import pytest

from cg.services.fastq_concatenation_service.fastq_concatenation_service import (
    FastqConcatenationService,
)


@pytest.fixture
def fastq_file_service():
    return FastqConcatenationService()


def create_fastqs_directory(number_forward_reads, number_reverse_reads, tmp_path):
    fastq_dir = Path(tmp_path, "fastqs")
    fastq_dir.mkdir()
    for i in range(number_forward_reads):
        file = Path(fastq_dir, f"sample_R1_{i}.fastq.gz")
        file.write_text(f"forward read {i}")

    for i in range(number_reverse_reads):
        file = Path(fastq_dir, f"sample_R2_{i}.fastq.gz")
        file.write_text(f"reverse read {i}")
    return fastq_dir


@pytest.fixture
def fastqs_dir(tmp_path) -> Path:
    return create_fastqs_directory(
        number_forward_reads=3, number_reverse_reads=3, tmp_path=tmp_path
    )


@pytest.fixture
def fastqs_forward(tmp_path) -> Path:
    """Return a directory with only forward reads."""
    return create_fastqs_directory(
        number_forward_reads=3, number_reverse_reads=0, tmp_path=tmp_path
    )
