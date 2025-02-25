from pathlib import Path
import pytest

from cg.services.fastq_concatenation_service.fastq_concatenation_service import (
    FastqConcatenationService,
)


@pytest.fixture
def fastq_file_service():
    return FastqConcatenationService()


def create_fastqs_directory(tmp_path: Path):
    fastq_dir = Path(tmp_path, "fastqs")
    fastq_dir.mkdir()
    return fastq_dir


def create_fastq_files(
    fastq_dir: Path, number_forward_reads: int, number_reverse_reads: int, sample_id: str
):
    for i in range(number_forward_reads):
        file = Path(fastq_dir, f"{sample_id}_R1_{i}.fastq.gz")
        file.write_text(f"{sample_id} forward read {i}")

    for i in range(number_reverse_reads):
        file = Path(fastq_dir, f"{sample_id}_R2_{i}.fastq.gz")
        file.write_text(f"{sample_id} reverse read {i}")


@pytest.fixture
def fastqs_dir(tmp_path: Path, sample_id: str) -> Path:
    fastq_dir: Path = create_fastqs_directory(tmp_path=tmp_path)
    create_fastq_files(
        fastq_dir=fastq_dir, number_forward_reads=3, number_reverse_reads=3, sample_id=sample_id
    )
    return fastq_dir


@pytest.fixture
def fastq_dir_existing_concatenated_files(tmp_path: Path, sample_id: str) -> Path:
    fastq_dir: Path = create_fastqs_directory(tmp_path=tmp_path)
    create_fastq_files(
        fastq_dir=fastq_dir, number_forward_reads=3, number_reverse_reads=3, sample_id=sample_id
    )
    forward_output_path = Path(fastq_dir, "forward.fastq.gz")
    reverse_output_path = Path(fastq_dir, "reverse.fastq.gz")
    forward_output_path.write_text("Existing concatenated forward reads")
    reverse_output_path.write_text("Existing concatenated reverse reads")
    return fastq_dir


@pytest.fixture
def fastqs_forward(tmp_path: Path, sample_id: str) -> Path:
    """Return a directory with only forward reads."""
    fastq_dir: Path = create_fastqs_directory(tmp_path=tmp_path)
    create_fastq_files(
        fastq_dir=fastq_dir, number_forward_reads=3, number_reverse_reads=0, sample_id=sample_id
    )
    return fastq_dir


@pytest.fixture
def fastqs_multiple_samples(tmp_path: Path, sample_id: str, another_sample_id: str) -> Path:
    """Return a directory with fastq files for multiple samples."""
    fastq_dir: Path = create_fastqs_directory(tmp_path=tmp_path)
    create_fastq_files(
        fastq_dir=fastq_dir, number_forward_reads=3, number_reverse_reads=3, sample_id=sample_id
    )
    create_fastq_files(
        fastq_dir=fastq_dir,
        number_forward_reads=3,
        number_reverse_reads=3,
        sample_id=another_sample_id,
    )
    return fastq_dir
