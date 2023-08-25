from pathlib import Path

import pytest


@pytest.fixture(name="deliverable_id")
def fixture_deliverable_id() -> str:
    return "CASEID"


@pytest.fixture(name="file_format")
def fixture_file_format() -> str:
    return "tsv"


@pytest.fixture(name="step")
def fixture_step() -> str:
    return "fusioncatcher"


@pytest.fixture(name="non_existing_file")
def fixture_non_existing_file() -> str:
    return "PATHTOCASE/fusioncatcher/CASEID.fusioncatcher.fusion-genes.txt"


@pytest.fixture(name="empty_field")
def fixture_empty_field() -> str:
    return "~"


@pytest.fixture(name="existing_file")
def fixture_existing_file(rnafusion_dir: Path) -> Path:
    """Return the path to an existing file."""
    file_path = Path(rnafusion_dir, "any_file.txt")
    file_path.touch()
    return file_path
