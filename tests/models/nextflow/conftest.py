import pytest


@pytest.fixture(name="nextflow_deliverables")
def fixture_nextflow_deliverables() -> dict:
    return {
        "format": "tsv",
        "id": "CASEID",
        "path": "PATHTOCASE/fusioncatcher/CASEID.fusioncatcher.fusion-genes.txt",
        "path_index": "~",
        "step": "fusioncatcher",
        "tag": "fusioncatcher",
    }


@pytest.fixture(name="nextflow_deliverables_with_empty_entry")
def fixture_nextflow_deliverables_with_empty_entry() -> dict:
    return {
        "format": "",
        "id": "CASEID",
        "path": "PATHTOCASE/fusioncatcher/CASEID.fusioncatcher.fusion-genes.txt",
        "path_index": "~",
        "step": "fusioncatcher",
        "tag": "fusioncatcher",
    }


@pytest.fixture(name="nextflow_deliverables_with_faulty_entry")
def fixture_nextflow_deliverables_with_faulty_entry() -> dict:
    return {
        "faulty_header": "tsv",
        "id": "CASEID",
        "path": "PATHTOCASE/fusioncatcher/CASEID.fusioncatcher.fusion-genes.txt",
        "path_index": "~",
        "step": "fusioncatcher",
        "tag": "fusioncatcher",
    }
