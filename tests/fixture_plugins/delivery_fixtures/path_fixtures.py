"""Delivery API path fixtures."""

from pathlib import Path

import pytest


@pytest.fixture
def hk_bundles_dir(tmp_path: Path) -> Path:
    directory = Path(tmp_path, "housekeeper_bundles")
    directory.mkdir(parents=True, exist_ok=True)
    return directory


@pytest.fixture
def hk_bundles_sample_dir(hk_bundles_dir: Path, sample_id: str) -> Path:
    directory = Path(hk_bundles_dir, sample_id)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


@pytest.fixture
def hk_bundles_another_sample_dir(hk_bundles_dir: Path, another_sample_id: str) -> Path:
    directory = Path(hk_bundles_dir, another_sample_id)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


@pytest.fixture
def hk_bundles_case_dir(hk_bundles_dir: Path, case_id: str) -> Path:
    directory = Path(hk_bundles_dir, case_id)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


@pytest.fixture
def hk_fastq_sample_file(hk_bundles_sample_dir: Path, sample_id: str) -> Path:
    file = Path(hk_bundles_sample_dir, f"{sample_id}_R1.fastq.gz")
    file.touch()
    return file


@pytest.fixture
def hk_fastq_another_sample_file(
    hk_bundles_another_sample_dir: Path, another_sample_id: str
) -> Path:
    file = Path(hk_bundles_another_sample_dir, f"{another_sample_id}_R1.fastq.gz")
    file.touch()
    return file


@pytest.fixture
def hk_spring_sample_file(hk_bundles_sample_dir: Path, sample_id: str) -> Path:
    file = Path(hk_bundles_sample_dir, f"{sample_id}_S1.spring")
    file.touch()
    return file


@pytest.fixture
def hk_spring_another_sample_file(
    hk_bundles_another_sample_dir: Path, another_sample_id: str
) -> Path:
    file = Path(hk_bundles_another_sample_dir, f"{another_sample_id}_S1.spring")
    file.touch()
    return file


@pytest.fixture
def hk_case_report_file(hk_bundles_case_dir: Path, case_id: str) -> Path:
    file = Path(hk_bundles_case_dir, f"{case_id}_delivery-report.html")
    file.touch()
    return file


@pytest.fixture
def hk_sample_cram_file(hk_bundles_case_dir: Path, sample_id: str) -> Path:
    file = Path(hk_bundles_case_dir, f"{sample_id}.cram")
    file.touch()
    return file


@pytest.fixture
def hk_another_sample_cram_file(hk_bundles_case_dir: Path, another_sample_id: str) -> Path:
    file = Path(hk_bundles_case_dir, f"{another_sample_id}.cram")
    file.touch()
    return file
