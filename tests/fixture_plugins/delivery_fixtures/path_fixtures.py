"""Delivery API path fixtures."""

from pathlib import Path

import pytest


@pytest.fixture
def fastq_sample_file(tmp_path: Path, sample_id: str) -> Path:
    file = Path(tmp_path, f"{sample_id}_R1.fastq.gz")
    file.touch()
    return file


@pytest.fixture
def fastq_another_sample_file(tmp_path: Path, another_sample_id: str) -> Path:
    file = Path(tmp_path, f"{another_sample_id}_R1.fastq.gz")
    file.touch()
    return file


@pytest.fixture
def spring_sample_file(tmp_path: Path, sample_id: str) -> Path:
    file = Path(tmp_path, f"{sample_id}_S1.spring")
    file.touch()
    return file


@pytest.fixture
def spring_another_sample_file(tmp_path: Path, another_sample_id: str) -> Path:
    file = Path(tmp_path, f"{another_sample_id}_S1.spring")
    file.touch()
    return file


@pytest.fixture
def case_report_file(tmp_path: Path, case_id: str) -> Path:
    file = Path(tmp_path, f"{case_id}_delivery-report.html")
    file.touch()
    return file


@pytest.fixture
def sample_cram_file(tmp_path: Path, sample_id: str) -> Path:
    file = Path(tmp_path, f"{sample_id}.cram")
    file.touch()
    return file


@pytest.fixture
def another_sample_cram_file(tmp_path: Path, another_sample_id: str) -> Path:
    file = Path(tmp_path, f"{another_sample_id}.cram")
    file.touch()
    return file
