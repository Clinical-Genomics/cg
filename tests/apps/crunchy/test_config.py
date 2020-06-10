"""Tests for the config part of Crunchy"""

import pytest
from marshmallow import ValidationError

from cg.apps.crunchy.models import CrunchyFileSchema


def test_map_fastq_file_info(file_schema):
    """Test to validate file information with the schema"""
    # GIVEN some correct file informtion and a file schema
    file_info = {
        "path": "a_file.fastq.gz",
        "file": "first_read",
        "checksum": "checksum_first_read",
        "algorithm": "sha256",
    }
    # WHEN validating the file information
    result = file_schema.load(file_info)
    # THEN assert that the validation was succesfull
    assert result
    # THEN assert that the object is correct
    assert result["path"] == file_info["path"]


def test_map_fastq_file_info_missing_path(file_schema):
    """Test to validate invalid file information with the schema"""
    # GIVEN some file informtion without a path and a file schema
    file_info = {
        "file": "first_read",
        "checksum": "checksum_first_read",
        "algorithm": "sha256",
    }
    # WHEN validating the file information
    with pytest.raises(ValidationError):
        # THEN assert that the validation was not succesfull
        file_schema.load(file_info)


def test_map_multiple_files(spring_metadata, file_schema):
    """Test to map a list of some files on the file schema"""
    # GIVEN a list of files
    assert len(spring_metadata) > 1

    result = []
    # WHEN validating the file information
    for file_info in spring_metadata:
        result.append(file_schema.load(file_info))

    # THEN assert that the validation was succesfull
    assert result
    # THEN assert that all files exists after dumping
    assert len(result) == len(spring_metadata)


def test_map_multiple_files_at_once(spring_metadata):
    """Test to map a list of some files on the file schema"""
    # GIVEN a list of files
    assert len(spring_metadata) > 1
    file_schema = CrunchyFileSchema(many=True)
    # WHEN validating the file information
    result = file_schema.load(spring_metadata)

    # THEN assert that the validation was succesfull
    assert isinstance(result, list)
    # THEN assert that all files exists after dumping
    assert len(result) == len(spring_metadata)
