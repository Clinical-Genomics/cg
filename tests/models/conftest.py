"""Fixtures for the model tests"""
import gzip
import io
from pathlib import Path

import pytest


@pytest.fixture(name="content")
def fixture_content() -> str:
    """Return some content for a file"""
    _content = (
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt"
        " ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ull"
        "amco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehende"
        "rit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaec"
        "at cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."
    )
    return _content


@pytest.fixture(name="non_existing_file_path")
def fixture_non_existing_file_path(project_dir: Path) -> Path:
    """Return the path to a non existing file"""
    return project_dir / "a_file.txt"


@pytest.fixture(name="non_existing_gzipped_file_path")
def fixture_non_existing_gzipped_file_path(non_existing_file_path: Path) -> Path:
    """Return the path to a non existing file with gzipped ending"""
    return non_existing_file_path.with_suffix(".gz")


@pytest.fixture(name="filled_file")
def fixture_filled_file(non_existing_file_path: Path, content: str) -> Path:
    """Return the path to a existing file with some content"""
    with open(non_existing_file_path, "w") as outfile:
        outfile.write(content)
    return non_existing_file_path


@pytest.fixture(name="filled_gzip_file")
def fixture_filled_gzip_file(non_existing_gzipped_file_path: Path, content: str) -> Path:
    """Return the path to a existing file with some content that is gzipped"""
    with gzip.open(non_existing_gzipped_file_path, "wb") as outfile:
        with io.TextIOWrapper(outfile, encoding="utf-8") as enc:
            enc.write(content)
    return non_existing_gzipped_file_path


@pytest.fixture(scope="function", name="gzipped_empty_file")
def fixture_gzipped_empty_file(fastq_dir: Path) -> Path:
    """Return a the path to a file that is gzipped without any content

    This file will not have the size = 0 due to gzip header and footer
    """

    return fastq_dir / "dummy_run_R1_001.fastq.gz"
