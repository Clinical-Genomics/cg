"""Tests for SPRING decompression methods"""

import logging

import pytest

from cg.constants.constants import FileFormat
from cg.io.controller import ReadFile, WriteFile


def test_is_spring_decompression_done_all_files_exist(
    compression_object, spring_metadata_file, caplog
):
    """Test if SPRING decompression is done when FASTQ files are unarchived.

    The function should return true since both FASTQ files and SPRING files exists and there is an
    updated field in the SPRING metadata config.
    """
    caplog.set_level(logging.DEBUG)
    # GIVEN that the FASTQ paths exists
    compression_object.fastq_first.touch()
    compression_object.fastq_second.touch()
    # GIVEN a existing SPRING file
    compression_object.spring_path.touch()

    # GIVEN a existing flag file
    # GIVEN that the files have an updated tag
    old_date = "2019-01-01"
    content = ReadFile.get_content_from_file(
        file_format=FileFormat.JSON, file_path=spring_metadata_file
    )

    # GIVEN that the files where updated more than three weeks ago
    for file_info in content:
        file_info["updated"] = old_date
    WriteFile.write_file_from_content(
        content=content, file_format=FileFormat.JSON, file_path=spring_metadata_file
    )

    # WHEN checking if SPRING decompression is done
    result: bool = compression_object.is_spring_decompression_done

    # THEN result should be True since all files exists and has been updated
    assert result is True
    # THEN assert that it was communicated that decompression is done
    assert f"SPRING decompression is done for run {compression_object.run_name}" in caplog.text


def test_is_spring_decompression_done_missing_fastq_files(
    compression_object, spring_metadata_file, caplog
):
    """Test if SPRING decompression is done when FASTQ files are missing

    The function should return False since FASTQ files are missing
    """
    caplog.set_level(logging.DEBUG)
    # GIVEN that the FASTQ paths does not exist
    compression_object.fastq_first.unlink()
    compression_object.fastq_second.unlink()
    assert not compression_object.fastq_first.exists()
    assert not compression_object.fastq_second.exists()

    # GIVEN a existing SPRING file
    compression_object.spring_path.touch()

    # WHEN checking if SPRING decompression is done
    result: bool = compression_object.is_spring_decompression_done

    # THEN result should be False since FASTQ files are missing
    assert result is False
    # THEN assert that it was communicated that decompression is done
    assert "does not exist" in caplog.text


def test_is_spring_decompression_done_all_files_exist_not_updated(
    compression_object, spring_metadata_file, caplog
):
    """Test if SPRING decompression is done when FASTQ files are not unarchived

    The function should return False since the files has not been updated in the metadata file
    """
    caplog.set_level(logging.DEBUG)
    # GIVEN that the FASTQ paths exists
    compression_object.fastq_first.touch()
    compression_object.fastq_second.touch()
    # GIVEN a existing SPRING file
    compression_object.spring_path.touch()

    # GIVEN a existing flag file
    # GIVEN that the files are missing the updated tag
    content = ReadFile.get_content_from_file(
        file_format=FileFormat.JSON, file_path=spring_metadata_file
    )

    # GIVEN that the files where updated more than three weeks ago
    for file_info in content:
        assert "updated" not in file_info

    # WHEN checking if SPRING decompression is done
    result: bool = compression_object.is_spring_decompression_done

    # THEN result should be False since all files exists but miss the updated tag
    assert result is False
    # THEN assert that it was communicated that files have not been updated
    assert "Files have not been unarchived" in caplog.text


def test_is_spring_decompression_done_missing_metadata_file(compression_object, caplog):
    """Test if SPRING decompression is done when SPRING metadata file is missing

    The function should return False since no metadata file is found
    """
    caplog.set_level(logging.DEBUG)
    # GIVEN that the SPRING metadata file is missing
    assert not compression_object.spring_metadata_path.exists()

    # WHEN checking if SPRING decompression is done
    result: bool = compression_object.is_spring_decompression_done

    # THEN result should be False since the metadata file is missing
    assert result is False
    # THEN assert that it was communicated that files have not been updated
    assert "No SPRING metadata file found" in caplog.text


def test_is_spring_decompression_done_empty_metadata_file(compression_object, caplog):
    """Test if SPRING decompression is done when SPRING metadata file has no content

    The function should return False since the metadata file has no content
    """
    caplog.set_level(logging.DEBUG)

    # GIVEN that the SPRING metadata file has no content
    compression_object.spring_metadata_path.touch()

    # WHEN checking if SPRING decompression is done
    with pytest.raises(SyntaxError):
        # THEN assert that an exception should be raised since the file is malformed
        compression_object.is_spring_decompression_done
        # THEN assert that it was communicated that the content is malformed
        assert "Malformed metadata content" in caplog.text


def test_is_spring_decompression_possible_false(compression_object, spring_metadata_file):
    """Test if SPRING decompression is possible when decompression is already done

    The function should return False since decompression is already done
    """
    # GIVEN that the FASTQ paths exists
    compression_object.fastq_first.touch()
    compression_object.fastq_second.touch()
    # GIVEN a existing SPRING file
    compression_object.spring_path.touch()

    # GIVEN a existing flag file
    # GIVEN that the files have an updated tag
    old_date = "2019-01-01"
    content = ReadFile.get_content_from_file(
        file_format=FileFormat.JSON, file_path=spring_metadata_file
    )

    # GIVEN that the files where updated more than three weeks ago
    for file_info in content:
        file_info["updated"] = old_date
    WriteFile.write_file_from_content(
        content=content, file_format=FileFormat.JSON, file_path=spring_metadata_file
    )

    # WHEN checking if SPRING decompression is possible
    result: bool = compression_object.is_spring_decompression_possible

    # THEN result should be False since decompression is already done
    assert result is False


def test_is_spring_decompression_possible_decompression_pending(
    compression_object, spring_metadata_file, caplog
):
    """Test if SPRING decompression is possible when decompression is pending

    The function should return False since decompression is pending
    """
    caplog.set_level(logging.DEBUG)
    # GIVEN a existing pending file
    compression_object.pending_path.touch()

    # WHEN checking if SPRING decompression is possible
    result = compression_object.is_spring_decompression_possible

    # THEN result should be False since decompression is pending
    assert result is False
    # THEN assert that it was communicated that compression is pending
    assert "decompression is pending" in caplog.text


def test_is_spring_decompression_possible_true(compression_object, spring_metadata_file, caplog):
    """Test if SPRING decompression is possible

    The function should return True since there is a SPRING file and no FASTQ files
    """
    caplog.set_level(logging.DEBUG)
    # GIVEN a existing SPRING file
    compression_object.spring_path.touch()
    # GIVEN that the FASTQ files does not exist
    compression_object.fastq_first.unlink()
    compression_object.fastq_second.unlink()
    assert not compression_object.fastq_first.exists()
    assert not compression_object.fastq_second.exists()

    # WHEN checking if SPRING decompression is possible
    result = compression_object.is_spring_decompression_possible

    # THEN result should be True since decompression is possible
    assert result is True
    # THEN assert that it was communicated that compression is pending
    assert "Decompression is possible" in caplog.text
