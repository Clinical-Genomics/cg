from pathlib import Path

import pytest


@pytest.fixture
def csv_file_path(fixtures_dir: Path) -> Path:
    """Return a file path to example CSV file."""
    return Path(fixtures_dir, "io", "example.csv")


@pytest.fixture
def csv_stream() -> str:
    """Return string with CSV format."""
    return """Lorem,ipsum,sit,amet"""


@pytest.fixture
def csv_temp_path(cg_dir: Path) -> Path:
    """Return a temp file path to use when writing csv."""
    return Path(cg_dir, "write.csv")
