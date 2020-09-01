"""Tests for the file data class"""
import pytest

from cg.models.file_data import FileData


def test_is_gzipped(filled_gzip_file):
    """Test if a file that is gzipped is gzipped"""
    # GIVEN an existing gzipped file
    assert filled_gzip_file.exists()
    # GIVEN a gzipped file with content
    assert filled_gzip_file.stat().st_size > 0

    # WHEN checking if the file is gzipped
    res = FileData.is_gzipped(filled_gzip_file)

    # THEN assert the result is True
    assert res is True


def test_is_gzipped_non_zipped(filled_file):
    """Test if a file that is not gzipped is gzipped"""
    # GIVEN an existing file that is not compressed
    assert filled_file.exists()
    # GIVEN a gzipped file with content
    assert filled_file.stat().st_size > 0

    # WHEN checking if the file is gzipped
    res = FileData.is_gzipped(filled_file)

    # THEN assert the result is False
    assert res is False


def test_is_gzipped_non_existing(non_existing_gzipped_file_path):
    """Test if a file that does not exist is gzipped"""
    # GIVEN an non existing file
    assert not non_existing_gzipped_file_path.exists()

    # WHEN checking if the file is gzipped
    with pytest.raises(FileNotFoundError):
        # THEN assert that a FileNotFoundError is raised
        FileData.is_gzipped(non_existing_gzipped_file_path)


def test_is_gzipped_empty_file(non_existing_gzipped_file_path):
    """Test if a file that does exists but is empty"""
    # GIVEN an existing file
    non_existing_gzipped_file_path.touch()
    gzipped_file_path = non_existing_gzipped_file_path
    assert gzipped_file_path.exists()
    # GIVEN a gzipped file without content
    assert gzipped_file_path.stat().st_size == 0

    # WHEN checking if the file is gzipped
    res = FileData.is_gzipped(gzipped_file_path)

    # THEN assert result is False
    assert res is False


def test_is_empty_file(non_existing_gzipped_file_path):
    """Test if a file that is empty is evaluated as empty"""
    # GIVEN an existing file
    non_existing_gzipped_file_path.touch()
    gzipped_file_path = non_existing_gzipped_file_path
    assert gzipped_file_path.exists()
    # GIVEN a gzipped file without content
    assert gzipped_file_path.stat().st_size == 0

    # WHEN checking if the file is empty
    res = FileData.is_empty(gzipped_file_path)

    # THEN assert result is True
    assert res is True


def test_is_empty_file_not_empty(filled_gzip_file):
    """Test if a file that is not empty is evaluated as empty"""
    # GIVEN a gzipped file with content
    assert filled_gzip_file.stat().st_size > 0

    # WHEN checking if the file is empty
    res = FileData.is_empty(filled_gzip_file)

    # THEN assert result is False
    assert res is False
