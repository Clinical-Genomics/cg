import pytest


@pytest.fixture
def expected_raredisease_workflow_params_content() -> dict:
    """Return a dictionary with some parameters for the raredisease params file."""
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
