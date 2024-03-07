"""Delivery API path fixtures."""

from pathlib import Path

import pytest


@pytest.fixture
def delivery_fastq_file(tmp_path: Path, sample_id: str) -> Path:
    file = Path(tmp_path, f"{sample_id}_R1.fastq.gz")
    file.touch()
    return file


@pytest.fixture
def delivery_another_fastq_file(tmp_path: Path, another_sample_id: str) -> Path:
    file = Path(tmp_path, f"{another_sample_id}_R1.fastq.gz")
    file.touch()
    return file


@pytest.fixture
def delivery_spring_file(tmp_path: Path, sample_id: str) -> Path:
    file = Path(tmp_path, f"{sample_id}_S1.spring")
    file.touch()
    return file


@pytest.fixture
def delivery_another_spring_file(tmp_path: Path, another_sample_id: str) -> Path:
    file = Path(tmp_path, f"{another_sample_id}_S1.spring")
    file.touch()
    return file


@pytest.fixture
def delivery_report_file(tmp_path: Path, case_id: str) -> Path:
    file = Path(tmp_path, f"{case_id}_delivery-report.html")
    file.touch()
    return file


@pytest.fixture
def delivery_cram_file(tmp_path: Path, sample_id: str) -> Path:
    file = Path(tmp_path, f"{sample_id}.cram")
    file.touch()
    return file


@pytest.fixture
def delivery_another_cram_file(tmp_path: Path, another_sample_id: str) -> Path:
    file = Path(tmp_path, f"{another_sample_id}.cram")
    file.touch()
    return file
