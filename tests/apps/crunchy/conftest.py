"""Fixtures for crunchy API."""
import logging
from pathlib import Path
from typing import List, Dict

import pytest

from cg.constants.constants import FileFormat
from cg.io.controller import WriteFile
from cg.models import CompressionData
from cgmodels.crunchy.metadata import CrunchyMetadata

LOG = logging.getLogger(__name__)


@pytest.fixture(name="real_spring_metadata_path")
def fixture_real_spring_metadata_path(apps_dir: Path) -> Path:
    """Return the path to a SPRING metadata file."""
    return Path(apps_dir, "crunchy", "spring_metadata.json")


@pytest.fixture(name="spring_metadata")
def fixture_spring_metadata(compression_object: CompressionData) -> List[dict]:
    """Return meta data information."""
    return [
        {
            "path": compression_object.fastq_first.as_posix(),
            "file": "first_read",
            "checksum": "checksum_first_read",
            "algorithm": "sha256",
        },
        {
            "path": compression_object.fastq_second.as_posix(),
            "file": "second_read",
            "checksum": "checksum_second_read",
            "algorithm": "sha256",
        },
        {"path": compression_object.spring_path.as_posix(), "file": "spring"},
    ]


@pytest.fixture(name="crunchy_metadata_object")
def fixture_crunchy_metadata_object(spring_metadata: List[dict]) -> CrunchyMetadata:
    """Return Crunchy metadata."""
    return CrunchyMetadata(files=spring_metadata)


@pytest.fixture(name="spring_metadata_file")
def fixture_spring_metadata_file(
    compression_object: CompressionData, spring_metadata: List[dict]
) -> Path:
    """Return the path to a populated SPRING metadata file."""
    metadata_path = compression_object.spring_metadata_path
    WriteFile.write_file_from_content(
        content=spring_metadata, file_format=FileFormat.JSON, file_path=metadata_path
    )
    return metadata_path


@pytest.fixture(name="fastq_first_file")
def fixture_fastq_first_file(fastq_first_path: Path) -> Path:
    """Creates an existing FASTQ path."""
    fastq_first_path.touch()
    return fastq_first_path


@pytest.fixture(name="fastq_second_file")
def fixture_fastq_second_file(fastq_second_path: Path) -> Path:
    """Creates an existing FASTQ path."""
    fastq_second_path.touch()
    return fastq_second_path


@pytest.fixture(name="spring_file")
def fixture_spring_file(spring_path: Path) -> Path:
    """Creates an existing SPRING file."""
    spring_path.touch()
    return spring_path


@pytest.fixture(name="fastq_paths")
def fixture_fastq_paths(fastq_first_path: Path, fastq_second_path: Path) -> Dict[str, Path]:
    """Creates FASTQ paths."""
    return {
        "fastq_first_path": fastq_first_path,
        "fastq_second_path": fastq_second_path,
    }


@pytest.fixture(name="existing_fastq_paths")
def fixture_existing_fastq_paths(
    fastq_first_file: Path, fastq_second_file: Path
) -> Dict[str, Path]:
    """Creates existing FASTQ paths."""
    return {
        "fastq_first_path": fastq_first_file,
        "fastq_second_path": fastq_second_file,
    }
