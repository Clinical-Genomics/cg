from pathlib import Path

import pytest


@pytest.fixture
def raredisease_case_path(raredisease_dir: Path, raredisease_case_id: str) -> Path:
    return Path(raredisease_dir, raredisease_case_id)


@pytest.fixture
def nextflow_case_path(nextflow_root: str, nextflow_case_id) -> Path:
    return Path(nextflow_root, nextflow_case_id)


@pytest.fixture
def nextflow_sample_sheet_path() -> Path:
    """Path to sample sheet."""
    return Path("samplesheet", "path")


@pytest.fixture
def fastq_path_1() -> Path:
    return Path("path", "fastq_1.fastq.gz")


@pytest.fixture
def fastq_path_2() -> Path:
    return Path("path", "fastq_2.fastq.gz")
