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
def raredisease_config_profiles() -> list[str]:
    return ["myprofile"]


@pytest.fixture
def nextflow_workflow_params_content() -> dict:
    """Return a dictionary with some parameters for the Nextflow params file."""
    return {"someparam": "something"}


@pytest.fixture
def expected_raredisease_params_content() -> dict:
    """Return a dictionary with some parameters for the Raredisease params file."""
    return {
        "input": "/path/to/samplesheet/case_samplesheet.csv",
        "outdir": "/path/to/case",
        "genomes_base": "/path/to/pipeline/version",
        "all": False,
        "arriba": True,
        "cram": "arriba,starfusion",
        "fastp_trim": True,
        "fusioncatcher": True,
        "starfusion": True,
        "trim_tail": 50,
    }
