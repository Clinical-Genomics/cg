"""Tests for the config part of Crunchy"""
import json
from pathlib import Path

from cg.apps.crunchy.files import get_crunchy_metadata, update_metadata_date
from cgmodels.crunchy.metadata import CrunchyMetadata


def test_get_spring_metadata_real_file(real_spring_metadata_path: Path, crunchy_config_dict: dict):
    """Test to parse the content of a real spring metadata file"""
    # GIVEN the path to a file with spring metadata content
    with open(real_spring_metadata_path, "r") as infile:
        content = json.load(infile)

    # WHEN parsing the content
    crunchy_metadata: CrunchyMetadata = get_crunchy_metadata(real_spring_metadata_path)

    # THEN assert the content is the same
    assert len(content) == len(crunchy_metadata.files)


def test_update_date(spring_metadata_file: Path, crunchy_config_dict: dict):
    """Test to update the date in a spring metadata file"""
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
