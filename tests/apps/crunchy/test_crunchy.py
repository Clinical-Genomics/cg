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


def test_is_fastq_compression_possible(crunchy_config_dict, compression_object, caplog):
    """test if fastq compression is possible when situation is like it should be

    This means that there should exist fastq files but no spring file
    """
    caplog.set_level(logging.DEBUG)
    # GIVEN a crunchy-api, and existing fastq paths
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    compression_object.fastq_first.touch()
    compression_object.fastq_second.touch()
    # GIVEN no spring file exists
    spring_file = compression_object.spring_path
    assert not spring_file.exists()

    # WHEN checking if spring compression is done
    result = crunchy_api.is_fastq_compression_possible(compression_object)

    # THEN result should be True
    assert result is True
    # THEN assert that the correct message was communicated
    assert "Fastq compression is possible" in caplog.text


def test_is_fastq_compression_possible_compression_pending(
    crunchy_config_dict, compression_object, caplog
):
    """test if fastq compression is possible when fastq compression is pending

    This means that there should exist a fastq compression flag
    """
    caplog.set_level(logging.DEBUG)
    # GIVEN a crunchy-api, and existing fastq paths
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    compression_object.fastq_first.touch()
    compression_object.fastq_second.touch()
    # GIVEN that the pending path exists
    compression_object.pending_path.touch()
    # GIVEN no spring file exists
    spring_file = compression_object.spring_path
    assert not spring_file.exists()

    # WHEN checking if spring compression is done
    result = crunchy_api.is_fastq_compression_possible(compression_object)

    # THEN result should be False since the compression flag exists
    assert result is False
    # THEN assert that the correct message was communicated
    assert "Compression/decompression is pending for" in caplog.text


def test_is_fastq_compression_possible_spring_exists(
    crunchy_config_dict, compression_object, caplog
):
    """test if fastq compression is possible when fastq compression is done

    This means that the spring file exists
    """
    caplog.set_level(logging.DEBUG)
    # GIVEN a crunchy-api, and existing fastq paths
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    # GIVEN that the spring path exists
    compression_object.spring_path.touch()
    spring_file = compression_object.spring_path
    assert spring_file.exists()

    # WHEN checking if spring compression is done
    result = crunchy_api.is_fastq_compression_possible(compression_object)

    # THEN result should be False since the compression flag exists
    assert result is False
    # THEN assert that the correct message was communicated
    assert "SPRING file found" in caplog.text


def test_is_compression_done(crunchy_config_dict, spring_metadata_file, compression_object, caplog):
    """test if compression is done when everything is correct"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a crunchy-api, and fastq paths
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    # GIVEN no spring file exists
    compression_object.spring_path.touch()
    assert spring_metadata_file == compression_object.spring_metadata_path
    assert spring_metadata_file.exists()

    # WHEN checking if spring compression is done
    result = crunchy_api.is_fastq_compression_done(compression_object)

    # THEN result should be True
    assert result is True
    # THEN assert that the correct message was communicated
    assert "Fastq compression is done" in caplog.text


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
    assert spring_metadata_file == compression_object.spring_metadata_path
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
    assert spring_metadata_file == compression_object.spring_metadata_path
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
    """Test if compression is done when fastq files are updated a long time ago

    The function should return True since files are old
    """
    caplog.set_level(logging.DEBUG)
    # GIVEN a crunchy-api, and fastq paths
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    # GIVEN a existing spring file
    compression_object.spring_path.touch()
    assert compression_object.spring_path.exists()
    # GIVEN a existing flag file
    metadata_file = compression_object.spring_metadata_path
    assert spring_metadata_file == compression_object.spring_metadata_path
    assert metadata_file.exists()

    # GIVEN that the files where updated less than three weeks ago
    crunchy_api.update_metadata_date(metadata_file)
    with open(metadata_file, "r") as infile:
        content = json.load(infile)
    for file_info in content:
        file_info["updated"] = "2019-01-01"

    with open(metadata_file, "w") as outfile:
        outfile.write(json.dumps(content))

    # WHEN checking if spring compression is done
    result = crunchy_api.is_fastq_compression_done(compression_object)

    # THEN result should be True since the updated date > 3 weeks
    assert result is True
    # THEN assert that correct information is logged
    assert "Fastq compression is done" in caplog.text


def test_is_spring_decompression_possible_no_fastq(crunchy_config_dict, compression_object, caplog):
    """Test if decompression is possible when there are no fastq files

    The function should return true since there are no fastq files
    """
    caplog.set_level(logging.DEBUG)
    # GIVEN a crunchy-api, and fastq paths
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    # GIVEN a existing spring file
    compression_object.spring_path.touch()
    assert compression_object.spring_path.exists()

    # WHEN checking if spring compression is done
    result = crunchy_api.is_spring_decompression_possible(compression_object)

    # THEN result should be True since the files are older than 3 weeks
    assert result is True
    # THEN assert the correct information is communicated
    assert "Decompression is possible" in caplog.text


def test_is_spring_decompression_possible_no_spring(
    crunchy_config_dict, compression_object, caplog
):
    """Test if decompression is possible when there are is spring archive

    The function should return False since there is no spring archive
    """
    caplog.set_level(logging.DEBUG)
    # GIVEN a crunchy-api, and fastq paths
    crunchy_api = CrunchyAPI(crunchy_config_dict)

    # WHEN checking if spring compression is done
    result = crunchy_api.is_spring_decompression_possible(compression_object)

    # THEN result should be False since there is no spring archive
    assert result is False
    # THEN assert the correct information is communicated
    assert "No SPRING file found" in caplog.text


def test_is_spring_decompression_possible_fastq(crunchy_config_dict, compression_object, caplog):
    """Test if decompression is possible when there are existing fastq files

    The function should return False since there are decompressed fastq files
    """
    caplog.set_level(logging.DEBUG)
    # GIVEN a crunchy-api, and fastq paths
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    # GIVEN a existing spring file
    compression_object.spring_path.touch()
    # GIVEN that the fastq files exists
    compression_object.fastq_first.touch()
    compression_object.fastq_second.touch()

    # WHEN checking if spring decompression is possible
    result = crunchy_api.is_spring_decompression_possible(compression_object)

    # THEN result should be False since the fastq files already exists
    assert result is False
    # THEN assert the correct information is communicated
    assert "Fastq files already exists" in caplog.text


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
