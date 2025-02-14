"""Delivery API path fixtures."""

from pathlib import Path

import pytest

from cg.constants import FileExtensions


@pytest.fixture
def delivery_fastq_file(tmp_path: Path, sample_id: str) -> Path:
    file = Path(tmp_path, f"FC_{sample_id}_L001_R1_001{FileExtensions.FASTQ_GZ}")
    file.touch()
    return file


@pytest.fixture
def delivery_case_fastq_file(tmp_path: Path, sample_id: str) -> Path:
    """
    This represents a fastq file stored on a case bundle. Mutant stored file like this in the past.
    This fixture servers the purpose to make sure these files are not fetched during delivery.
    """
    file = Path(tmp_path, f"{sample_id}_concat_{FileExtensions.FASTQ_GZ}")
    file.touch()
    return file


@pytest.fixture
def delivery_bam_file(tmp_path: Path, sample_id: str) -> Path:
    file = Path(tmp_path, f"{sample_id}_R1_001{FileExtensions.BAM}")
    file.touch()
    return file


@pytest.fixture
def delivery_another_fastq_file(tmp_path: Path, another_sample_id: str) -> Path:
    file = Path(tmp_path, f"FC_{another_sample_id}L001_R1_001{FileExtensions.FASTQ_GZ}")
    file.touch()
    return file


@pytest.fixture
def delivery_another_case_fastq_file(tmp_path: Path, another_sample_id: str) -> Path:
    """
    This represents a fastq file stored on a case bundle. Mutant stored file like this in the past.
    This fixture servers the purpose to make sure these files are not fetched during delivery.
    """
    file = Path(tmp_path, f"{another_sample_id}_concat_{FileExtensions.FASTQ_GZ}")
    file.touch()
    return file


@pytest.fixture
def delivery_another_bam_file(tmp_path: Path, another_sample_id: str) -> Path:
    file = Path(tmp_path, f"{another_sample_id}_R1_001{FileExtensions.BAM}")
    file.touch()
    return file


@pytest.fixture
def delivery_spring_file(tmp_path: Path, sample_id: str) -> Path:
    file = Path(tmp_path, f"{sample_id}_S1_001{FileExtensions.SPRING}")
    file.touch()
    return file


@pytest.fixture
def delivery_another_spring_file(tmp_path: Path, another_sample_id: str) -> Path:
    file = Path(tmp_path, f"{another_sample_id}_S1_001{FileExtensions.SPRING}")
    file.touch()
    return file


@pytest.fixture
def delivery_report_file(tmp_path: Path, case_id: str) -> Path:
    file = Path(tmp_path, f"{case_id}_delivery-report{FileExtensions.HTML}")
    file.touch()
    return file


@pytest.fixture
def delivery_cram_file(tmp_path: Path, sample_id: str) -> Path:
    file = Path(tmp_path, f"{sample_id}{FileExtensions.CRAM}")
    file.touch()
    return file


@pytest.fixture
def delivery_another_cram_file(tmp_path: Path, another_sample_id: str) -> Path:
    file = Path(tmp_path, f"{another_sample_id}{FileExtensions.CRAM}")
    file.touch()
    return file


@pytest.fixture
def delivery_ticket_dir_path(tmp_path: Path, ticket_id: str) -> Path:
    return Path(tmp_path, ticket_id)


@pytest.fixture
def delivery_consensus_sample_file(tmp_path: Path, sample_id: str) -> Path:
    file = Path(tmp_path, f"{sample_id}_consensus_sample{FileExtensions.VCF}")
    file.touch()
    return file


@pytest.fixture
def delivery_another_consensus_sample_file(tmp_path: Path, another_sample_id: str) -> Path:
    file = Path(tmp_path, f"{another_sample_id}_consensus_sample{FileExtensions.VCF}")
    file.touch()
    return file


@pytest.fixture
def delivery_vcf_report_file(tmp_path: Path, sample_id: str) -> Path:
    file = Path(tmp_path, f"{sample_id}_vcf_report{FileExtensions.VCF}")
    file.touch()
    return file


@pytest.fixture
def delivery_another_vcf_report_file(tmp_path: Path, another_sample_id: str) -> Path:
    file = Path(tmp_path, f"{another_sample_id}_vcf_report{FileExtensions.VCF}")
    file.touch()
    return file
