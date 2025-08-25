import pytest


@pytest.fixture
def nextflow_case_id() -> str:
    """Fixture for a Nextflow case id."""
    return "case_id"


@pytest.fixture
def nextflow_root() -> str:
    return "/root"


@pytest.fixture
def nextflow_sample_id() -> str:
    """Fixture for a Nextflow sample id."""
    return "sample_id"


@pytest.fixture
def nextflow_repository() -> str:
    return "https://some_url"


@pytest.fixture
def nextflow_pipeline_revision() -> str:
    return "2.2.0"


@pytest.fixture
def nextflow_config_profiles() -> list[str]:
    return ["myprofile"]
