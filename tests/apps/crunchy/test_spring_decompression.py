"""Tests for SPRING decompression methods"""
import logging

import pytest
from cg.apps.crunchy import CrunchyAPI
from cg.constants.constants import FileFormat
from cg.io.controller import ReadFile, WriteFile


def test_is_spring_decompression_done_all_files_exist(
    crunchy_config: dict, compression_object, spring_metadata_file, caplog
):
    """Test if SPRING decompression is done when FASTQ files are unarchived

    The function should return true since both FASTQ files and SPRING files exists and there is an
    updated field in the SPRING metadata config.
    """
    caplog.set_level(logging.DEBUG)
    # GIVEN a crunchy-api
    crunchy_api = CrunchyAPI(crunchy_config)
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
    result = crunchy_api.is_spring_decompression_done(compression_object)

    # THEN result should be True since all files exists and has been updated
    assert result is True
    # THEN assert that it was communicated that decompression is done
    assert f"SPRING decompression is done for run {compression_object.run_name}" in caplog.text


def test_is_spring_decompression_done_missing_fastq_files(
    crunchy_config: dict, compression_object, spring_metadata_file, caplog
):
    """Test if SPRING decompression is done when FASTQ files are missing

    The function should return False since FASTQ files are missing
    """
    caplog.set_level(logging.DEBUG)
    # GIVEN a crunchy-api
    crunchy_api = CrunchyAPI(crunchy_config)
    # GIVEN that the FASTQ paths does not exist
    compression_object.fastq_first.unlink()
    compression_object.fastq_second.unlink()
    assert not compression_object.fastq_first.exists()
    assert not compression_object.fastq_second.exists()

    # GIVEN a existing SPRING file
    compression_object.spring_path.touch()

    # WHEN checking if SPRING decompression is done
    result = crunchy_api.is_spring_decompression_done(compression_object)

    # THEN result should be False since FASTQ files are missing
    assert result is False
    # THEN assert that it was communicated that decompression is done
    assert "does not exist" in caplog.text


def test_is_spring_decompression_done_all_files_exist_not_updated(
    crunchy_config: dict, compression_object, spring_metadata_file, caplog
):
    """Test if SPRING decompression is done when FASTQ files are not unarchived

    The function should return False since the files has not been updated in the metadata file
    """
    caplog.set_level(logging.DEBUG)
    # GIVEN a crunchy-api
    crunchy_api = CrunchyAPI(crunchy_config)
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
    result = crunchy_api.is_spring_decompression_done(compression_object)

    # THEN result should be False since all files exists but miss the updated tag
    assert result is False
    # THEN assert that it was communicated that files have not been updated
    assert "Files have not been unarchived" in caplog.text


def test_is_spring_decompression_done_missing_metadata_file(
    crunchy_config: dict, compression_object, caplog
):
    """Test if SPRING decompression is done when SPRING metadata file is missing

    The function should return False since no metadata file is found
    """
    caplog.set_level(logging.DEBUG)
    # GIVEN a crunchy-api
    crunchy_api = CrunchyAPI(crunchy_config)
    # GIVEN that the SPRING metadata file is missing
    assert not compression_object.spring_metadata_path.exists()

    # WHEN checking if SPRING decompression is done
    result = crunchy_api.is_spring_decompression_done(compression_object)

    # THEN result should be False since the metadata file is missing
    assert result is False
    # THEN assert that it was communicated that files have not been updated
    assert "No SPRING metadata file found" in caplog.text


def test_is_spring_decompression_done_empty_metadata_file(
    crunchy_config: dict, compression_object, caplog
):
    """Test if SPRING decompression is done when SPRING metadata file has no content

    The function should return False since the metadata file has no content
    """
    caplog.set_level(logging.DEBUG)
    # GIVEN a crunchy-api
    crunchy_api = CrunchyAPI(crunchy_config)
    # GIVEN that the SPRING metadata file has no content
    compression_object.spring_metadata_path.touch()

    # WHEN checking if SPRING decompression is done
    with pytest.raises(SyntaxError):
        # THEN assert that an exception should be raised since the file is malformed
        crunchy_api.is_spring_decompression_done(compression_object)
        # THEN assert that it was communicated that the content is malformed
        assert "Malformed metadata content" in caplog.text


def test_is_spring_decompression_possible(
    crunchy_config: dict, compression_object, spring_metadata_file
):
    """Test if SPRING decompression is possible when decompression is already done

    The function should return False since decompression is already done
    """
    # GIVEN a crunchy-api
    crunchy_api = CrunchyAPI(crunchy_config)
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
    result = crunchy_api.is_spring_decompression_possible(compression_object)

    # THEN result should be False since decompression is already done
    assert result is False


def test_is_spring_decompression_possible_decompression_pending(
    crunchy_config: dict, compression_object, spring_metadata_file, caplog
):
    """Test if SPRING decompression is possible when decompression is pending

    The function should return False since decompression is pending
    """
    caplog.set_level(logging.DEBUG)
    # GIVEN a crunchy-api
    crunchy_api = CrunchyAPI(crunchy_config)
    # GIVEN a existing pending file
    compression_object.pending_path.touch()

    # WHEN checking if SPRING decompression is done
    result = crunchy_api.is_spring_decompression_possible(compression_object)

    # THEN result should be False since decompression is pending
    assert result is False
    # THEN assert that it was communicated that compression is pending
    assert "decompression is pending" in caplog.text


def test_is_spring_decompression_possible(
    crunchy_config: dict, compression_object, spring_metadata_file, caplog
):
    """Test if SPRING decompression is possible

    The function should return True since there is a SPRING file and no FASTQ files
    """
    caplog.set_level(logging.DEBUG)
    # GIVEN a crunchy-api
    crunchy_api = CrunchyAPI(crunchy_config)
    # GIVEN a existing SPRING file
    compression_object.spring_path.touch()
    # GIVEN that the FASTQ files does not exist
    compression_object.fastq_first.unlink()
    compression_object.fastq_second.unlink()
    assert not compression_object.fastq_first.exists()
    assert not compression_object.fastq_second.exists()

    # WHEN checking if SPRING decompression is done
    result = crunchy_api.is_spring_decompression_possible(compression_object)

    # THEN result should be True since decompression is possible
    assert result is True
    # THEN assert that it was communicated that compression is pending
    assert "Decompression is possible" in caplog.text
