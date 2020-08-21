"""Tests for spring decompression methods"""
import json
import logging

from cg.apps.crunchy import CrunchyAPI


def test_is_spring_decompression_done_all_files_exist(
    crunchy_config_dict, compression_object, spring_metadata_file, caplog
):
    """Test if spring decompression is done when fastq files are updated

    The function should return true since both fastq files and spring files exists and there is an
    updated field in the spring metadata config.
    """
    caplog.set_level(logging.DEBUG)
    # GIVEN a crunchy-api
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    # GIVEN that the fastq paths exists
    compression_object.fastq_first.touch()
    compression_object.fastq_second.touch()
    # GIVEN a existing spring file
    compression_object.spring_path.touch()

    # GIVEN a existing flag file
    # GIVEN that the files have an updated tag
    old_date = "2019-01-01"
    with open(spring_metadata_file, "r") as infile:
        content = json.load(infile)
    # GIVEN that the files where updated more than three weeks ago
    for file_info in content:
        file_info["updated"] = old_date
    with open(spring_metadata_file, "w") as outfile:
        outfile.write(json.dumps(content))

    # WHEN checking if spring decompression is done
    result = crunchy_api.is_spring_decompression_done(compression_object)

    # THEN result should be True since all files exists and has been updated
    assert result is True
    # THEN assert that it was communicated that decompression is done
    assert f"Spring decompression is ready for run {compression_object.run_name}" in caplog.text


def test_is_spring_decompression_done_missing_fastq_files(
    crunchy_config_dict, compression_object, spring_metadata_file, caplog
):
    """Test if spring decompression is done when fastq files are missing

    The function should return False since fastq files are missing
    """
    caplog.set_level(logging.DEBUG)
    # GIVEN a crunchy-api
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    # GIVEN that the fastq paths does not exist
    # GIVEN a existing spring file
    compression_object.spring_path.touch()

    # WHEN checking if spring decompression is done
    result = crunchy_api.is_spring_decompression_done(compression_object)

    # THEN result should be False since fastq files are missing
    assert result is False
    # THEN assert that it was communicated that decompression is done
    assert "does not exist" in caplog.text


def test_is_spring_decompression_done_all_files_exist_not_updated(
    crunchy_config_dict, compression_object, spring_metadata_file, caplog
):
    """Test if spring decompression is done when fastq files are not updated

    The function should return False since the files has not been updated in the metadata file
    """
    caplog.set_level(logging.DEBUG)
    # GIVEN a crunchy-api
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    # GIVEN that the fastq paths exists
    compression_object.fastq_first.touch()
    compression_object.fastq_second.touch()
    # GIVEN a existing spring file
    compression_object.spring_path.touch()

    # GIVEN a existing flag file
    # GIVEN that the files are missing the updated tag
    with open(spring_metadata_file, "r") as infile:
        content = json.load(infile)
    # GIVEN that the files where updated more than three weeks ago
    for file_info in content:
        assert "updated" not in file_info

    # WHEN checking if spring decompression is done
    result = crunchy_api.is_spring_decompression_done(compression_object)

    # THEN result should be True since all files exists and has been updated
    assert result is False
    # THEN assert that it was communicated that files have not been updated
    assert "Files have not been updated" in caplog.text


def test_is_spring_decompression_done_missing_metadata_file(
    crunchy_config_dict, compression_object, caplog
):
    """Test if spring decompression is done when fastq files are not updated

    The function should return False since the files has not been updated in the metadata file
    """
    caplog.set_level(logging.DEBUG)
    # GIVEN a crunchy-api
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    # GIVEN that the spring metadata file is missing
    assert not compression_object.spring_metadata_path.exists()

    # WHEN checking if spring decompression is done
    result = crunchy_api.is_spring_decompression_done(compression_object)

    # THEN result should be False since the metadata file is missing
    assert result is False
    # THEN assert that it was communicated that files have not been updated
    assert "No SPRING metadata file found" in caplog.text


def test_is_spring_decompression_done_empty_metadata_file(
    crunchy_config_dict, compression_object, caplog
):
    """Test if spring decompression is done when fastq files are not updated

    The function should return False since the files has not been updated in the metadata file
    """
    caplog.set_level(logging.DEBUG)
    # GIVEN a crunchy-api
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    # GIVEN that the spring metadata file is missing
    compression_object.spring_metadata_path.touch()

    # WHEN checking if spring decompression is done
    result = crunchy_api.is_spring_decompression_done(compression_object)

    # THEN result should be False since the metadata file has no content
    assert result is False
    # THEN assert that it was communicated that the content is malformed
    assert "Malformed metadata content" in caplog.text
