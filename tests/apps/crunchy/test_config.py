"""Tests the config part of Crunchy."""

from pathlib import Path
from typing import Any

from cg.apps.crunchy.files import (
    get_crunchy_metadata,
    update_metadata_date,
    update_metadata_paths,
)
from cg.apps.crunchy.models import CrunchyMetadata
from cg.constants.constants import FileFormat
from cg.io.controller import ReadFile


def test_get_spring_metadata_real_file(
    real_spring_metadata_path: Path, crunchy_config: dict[str, dict[str, Any]]
):
    """Test to parse the content of a real spring metadata file."""
    # GIVEN the path to a file with spring metadata content
    content: list = ReadFile.get_content_from_file(
        file_format=FileFormat.JSON, file_path=real_spring_metadata_path
    )

    # WHEN parsing the content
    crunchy_metadata: CrunchyMetadata = get_crunchy_metadata(real_spring_metadata_path)

    # THEN assert the length is the same
    assert len(content) == len(crunchy_metadata.files)


def test_update_date(spring_metadata_file: Path):
    """Test to update the date in a spring metadata file."""
    # GIVEN the path to a metadata file without any "updated" information and a crunchy api
    spring_metadata: CrunchyMetadata = get_crunchy_metadata(spring_metadata_file)
    for file_info in spring_metadata.files:
        assert file_info.updated is None

    # WHEN running the update date function
    update_metadata_date(spring_metadata_file)

    # THEN assert that the "updated" information has been added
    updated_spring_metadata: CrunchyMetadata = get_crunchy_metadata(spring_metadata_file)
    for file_info in updated_spring_metadata.files:
        assert file_info.updated is not None


def test_update_metadata_paths(spring_metadata_file: Path, fixtures_dir: Path):
    """Test to update paths in a spring metadata file."""
    # GIVEN the path to a metadata file without any "updated" information and a crunchy api

    # WHEN running the update date function
    update_metadata_paths(spring_metadata_path=spring_metadata_file, new_parent_path=fixtures_dir)

    # THEN assert that the parent path has been switched
    updated_spring_metadata: CrunchyMetadata = get_crunchy_metadata(spring_metadata_file)
    for file in updated_spring_metadata.files:
        assert Path(file.path).parent == fixtures_dir
