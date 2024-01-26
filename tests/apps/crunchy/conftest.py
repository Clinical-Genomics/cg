"""Fixtures for crunchy API."""

import logging
from pathlib import Path

import pytest

from cg.apps.crunchy.models import CrunchyMetadata
from cg.constants.constants import FileFormat
from cg.io.controller import WriteFile
from cg.models import CompressionData

LOG = logging.getLogger(__name__)


@pytest.fixture
def real_spring_metadata_path(apps_dir: Path) -> Path:
    """Return the path to a SPRING metadata file."""
    return Path(apps_dir, "crunchy", "spring_metadata.json")


@pytest.fixture
def spring_metadata(compression_object: CompressionData) -> list[dict]:
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


@pytest.fixture
def crunchy_metadata_object(spring_metadata: list[dict]) -> CrunchyMetadata:
    """Return Crunchy metadata."""
    return CrunchyMetadata(files=spring_metadata)


@pytest.fixture
def spring_metadata_file(compression_object: CompressionData, spring_metadata: list[dict]) -> Path:
    """Return the path to a populated SPRING metadata file."""
    metadata_path = compression_object.spring_metadata_path
    WriteFile.write_file_from_content(
        content=spring_metadata, file_format=FileFormat.JSON, file_path=metadata_path
    )
    return metadata_path
