import pytest


@pytest.fixture
def nextflow_case_id() -> str:
    """Fixture for a Nextflow case id."""
    return "case_id"


@pytest.fixture
def nextflow_sample_id() -> str:
    """Fixture for a Nextflow sample id."""
    return "sample_id"
