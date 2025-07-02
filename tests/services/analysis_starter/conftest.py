from pathlib import Path

import pytest


@pytest.fixture
def nextflow_case_id() -> str:
    """Fixture for a Nextflow case id."""
    return "case_id"


@pytest.fixture
def nextflow_case_path() -> Path:
    return Path("case", "path")


@pytest.fixture
def nextflow_sample_sheet_path() -> Path:
    """Path to sample sheet."""
    return Path("samplesheet", "path")
