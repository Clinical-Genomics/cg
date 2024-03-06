"""Delivery API path fixtures."""

from pathlib import Path

import pytest


@pytest.fixture
def fastq_sample_file(housekeeper_bundles_dir: Path, sample_id: str) -> Path:
    file = Path(housekeeper_bundles_dir, f"{sample_id}_R1.fastq.gz")
    file.touch()
    return file


@pytest.fixture
def fastq_another_sample_file(housekeeper_bundles_dir: Path, another_sample_id: str) -> Path:
    file = Path(housekeeper_bundles_dir, f"{another_sample_id}_R1.fastq.gz")
    file.touch()
    return file


@pytest.fixture
def spring_sample_file(housekeeper_bundles_dir: Path, sample_id: str) -> Path:
    file = Path(housekeeper_bundles_dir, f"{sample_id}_S1.spring")
    file.touch()
    return file


@pytest.fixture
def spring_another_sample_file(housekeeper_bundles_dir: Path, another_sample_id: str) -> Path:
    file = Path(housekeeper_bundles_dir, f"{another_sample_id}_S1.spring")
    file.touch()
    return file
