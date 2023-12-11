"""Fixtures for the model tests"""
import gzip
import io
from pathlib import Path

import pytest


@pytest.fixture(name="non_existing_gzipped_file_path")
def non_existing_gzipped_file_path(non_existing_file_path: Path) -> Path:
    """Return the path to a non existing file with gzipped ending"""
    return non_existing_file_path.with_suffix(".gz")


@pytest.fixture(name="filled_gzip_file")
def filled_gzip_file(non_existing_gzipped_file_path: Path, content: str) -> Path:
    """Return the path to a existing file with some content that is gzipped"""
    with gzip.open(non_existing_gzipped_file_path, "wb") as outfile:
        with io.TextIOWrapper(outfile, encoding="utf-8") as enc:
            enc.write(content)
    return non_existing_gzipped_file_path


@pytest.fixture(scope="function")
def gzipped_empty_file(fastq_dir: Path) -> Path:
    """Return a the path to a file that is gzipped without any content

    This file will not have the size = 0 due to gzip header and footer
    """

    return fastq_dir / "dummy_run_R1_001.fastq.gz"


@pytest.fixture
def fast_file_meta_raw(flow_cell_name: str) -> dict:
    return {
        "path": Path("a", "file.fastq.gz"),
        "lane": str(1),
        "read_number": str(2),
        "flow_cell_id": flow_cell_name,
        "undetermined": None,
    }
