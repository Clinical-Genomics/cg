"""Tests for CrunchyAPI"""
import json
import logging

from cg.apps.crunchy import CrunchyAPI


def test_set_dry_run(crunchy_config_dict):
    """Test to set the dry run of the api"""
    # GIVEN a crunchy API where dry run is False
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    assert crunchy_api.dry_run is False

    # WHEN updating the dry run
    crunchy_api.set_dry_run(True)

    # THEN assert that the api has true dry run
    assert crunchy_api.dry_run is True


def test_is_compression_done_no_spring(crunchy_config_dict, compression_object, caplog):
    """test if compression is done when no spring file"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a crunchy-api, and fastq paths
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    # GIVEN no spring file exists
    spring_file = compression_object.spring_path
    assert not spring_file.exists()

    # WHEN checking if spring compression is done
    result = crunchy_api.is_fastq_compression_done(compression_object)

    # THEN result should be false
    assert not result
    # THEN assert that the correct message was communicated
    assert f"No SPRING file for {compression_object.run_name}" in caplog.text


def test_is_compression_done_no_flag_spring(crunchy_config_dict, compression_object, caplog):
    """test if spring compression is done when no metadata file"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a crunchy-api, and fastq paths
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    # GIVEN a existing spring file
    compression_object.spring_path.touch()
    assert compression_object.spring_path.exists()
    # GIVEN a non existing flag file
    assert not compression_object.spring_metadata_path.exists()

    # WHEN checking if spring compression is done
    result = crunchy_api.is_fastq_compression_done(compression_object)

    # THEN result should be false
    assert not result
    # THEN assert that the correct message was communicated
    assert "No metadata file found" in caplog.text


def test_is_compression_done_spring(
    crunchy_config_dict, compression_object, spring_metadata_file, caplog
):
    """test if compression is done when spring files exists"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a crunchy-api, and fastq paths
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    # GIVEN a existing spring file
    compression_object.spring_path.touch()
    assert compression_object.spring_path.exists()
    # GIVEN a existing flag file
    assert compression_object.spring_metadata_path.exists()

    # WHEN checking if spring compression is done
    result = crunchy_api.is_fastq_compression_done(compression_object)

    # THEN result should be True
    assert result
    # THEN assert that the correct message was communicated
    assert f"Fastq compression is done for {compression_object.run_name}" in caplog.text


def test_is_compression_done_spring_new_files(
    crunchy_config_dict, compression_object, spring_metadata_file, caplog
):
    """Test if compression is done when fastq files are updated

    This test should fail since the fastq files are new
    """
    caplog.set_level(logging.DEBUG)
    # GIVEN a crunchy-api, and fastq paths
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    # GIVEN a existing spring file
    compression_object.spring_path.touch()
    assert compression_object.spring_path.exists()
    # GIVEN a existing flag file
    metadata_file = compression_object.spring_metadata_path
    assert metadata_file.exists()

    # GIVEN that the files where updated less than three weeks ago
    crunchy_api.update_metadata_date(metadata_file)
    with open(metadata_file, "r") as infile:
        content = json.load(infile)
    for file_info in content:
        assert "updated" in file_info

    # WHEN checking if spring compression is done
    result = crunchy_api.is_fastq_compression_done(compression_object)

    # THEN result should be False sinvce the updated date < 3 weeks
    assert result is False
    # THEN assert that correct information is logged
    assert "Fastq files are not old enough" in caplog.text


def test_is_compression_done_spring_old_files(
    crunchy_config_dict, compression_object, spring_metadata_file, caplog
):
    """Test if compression is done when fastq files are updated but old

    The function should return true since the files are older than 3 weeks
    """
    caplog.set_level(logging.DEBUG)
    # GIVEN a crunchy-api, and fastq paths
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    # GIVEN a existing spring file
    compression_object.spring_path.touch()
    assert compression_object.spring_path.exists()
    # GIVEN a existing flag file
    metadata_file = compression_object.spring_metadata_path
    assert metadata_file.exists()
    # GIVEN a date older than three weeks
    old_date = "2019-01-01"
    with open(metadata_file, "r") as infile:
        content = json.load(infile)
    # GIVEN that the files where updated more than three weeks ago
    for file_info in content:
        file_info["updated"] = old_date
    with open(metadata_file, "w") as outfile:
        outfile.write(json.dumps(content))

    # WHEN checking if spring compression is done
    result = crunchy_api.is_fastq_compression_done(compression_object)

    # THEN result should be True since the files are older than 3 weeks
    assert result is True


def test_is_not_pending(crunchy_config_dict, compression_object):
    """test if spring compression is pending"""
    # GIVEN a crunchy-api, and a fastq file
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    # GIVEN a non existing pending flag
    assert not compression_object.pending_path.exists()

    # WHEN checking if spring compression is done
    result = crunchy_api.is_compression_pending(compression_object)

    # THEN result should be False since the pending flag is not there
    assert result is False


def test_is_pending(crunchy_config_dict, compression_object):
    """test if spring compression is pending when pending file exists"""
    # GIVEN a crunchy-api, and fastq files
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    # GIVEN a existing pending flag
    compression_object.pending_path.touch()
    assert compression_object.pending_path.exists()

    # WHEN checking if spring compression is pending
    result = crunchy_api.is_compression_pending(compression_object)

    # THEN result should be True since the pending_path exists
    assert result is True
