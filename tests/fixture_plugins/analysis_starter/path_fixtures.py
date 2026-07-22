from pathlib import Path

import pytest


@pytest.fixture
def nextflow_case_path(nextflow_root: str, nextflow_case_id) -> Path:
    return Path(nextflow_root, nextflow_case_id)


@pytest.fixture
def fastq_path_1() -> Path:
    return Path("path", "fastq_1.fastq.gz")


@pytest.fixture
def fastq_path_2() -> Path:
    return Path("path", "fastq_2.fastq.gz")
