"""Tests for CrunchyAPI"""
import json
import logging
from pathlib import Path

from cg.apps.crunchy import CrunchyAPI
from cg.constants import FASTQ_FIRST_READ_SUFFIX, FASTQ_SECOND_READ_SUFFIX, SPRING_SUFFIX


def test_set_dry_run(crunchy_config_dict):
    """Test to set the dry run of the api"""
    # GIVEN a crunchy API where dry run is False
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    assert crunchy_api.dry_run is False

    # WHEN updating the dry run
    crunchy_api.set_dry_run(True)

    # THEN assert that the api has true dry run
    assert crunchy_api.dry_run is True


def test_get_flag_path_spring(crunchy_config_dict, project_dir):
    """Test get_flag_path for a spring file"""

    # GIVEN a spring path
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    spring_path = project_dir / "file.spring"

    # WHEN creating flag path
    flag_path = crunchy_api.get_flag_path(file_path=spring_path)

    # THEN this file should have a json prefix
    assert flag_path.suffixes == [".json"]


def test_fastq_to_spring(crunchy_config_dict, fastq_paths, mocker):
    """Test fastq_to_spring method"""

    # GIVEN a crunchy-api, and fastq paths
    mocker_submit_sbatch = mocker.patch.object(CrunchyAPI, "_submit_sbatch")
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    fastq_first = fastq_paths["fastq_first_path"]
    fastq_second = fastq_paths["fastq_second_path"]

    # WHEN calling fastq_to_spring on fastq files
    crunchy_api.fastq_to_spring(
        fastq_first=fastq_first, fastq_second=fastq_second,
    )

    # THEN _submit_sbatch method is called with expected sbatch-content
    mocker_submit_sbatch.assert_called()


def test_is_compression_done_no_spring(crunchy_config_dict, existing_fastq_paths):
    """test if compression is done when no spring file"""
    # GIVEN a crunchy-api, and fastq paths
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    fastq_first = existing_fastq_paths["fastq_first_path"]
    # GIVEN no spring file exists
    spring_file = CrunchyAPI.get_spring_path_from_fastq(fastq=fastq_first)
    assert not spring_file.exists()

    # WHEN checking if spring compression is done
    result = crunchy_api.is_spring_compression_done(fastq_first)

    # THEN result should be false
    assert not result


def test_is_compression_done_no_flag_spring(crunchy_config_dict, compressed_fastqs_without_flag):
    """test if spring compression is done when no flag"""
    # GIVEN a crunchy-api, and fastq paths
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    fastq_first = compressed_fastqs_without_flag["fastq_first_path"]
    # GIVEN a existing spring file
    spring_file = CrunchyAPI.get_spring_path_from_fastq(fastq=fastq_first)
    assert spring_file.exists()
    # GIVEN a non existing flag file
    flag_file = CrunchyAPI.get_flag_path(file_path=spring_file)
    assert not flag_file.exists()

    # WHEN checking if spring compression is done
    result = crunchy_api.is_spring_compression_done(fastq_first)

    # THEN result should be false
    assert not result


def test_is_compression_done_spring(crunchy_config_dict, compressed_fastqs):
    """test if compression is done when spring file exists"""
    # GIVEN a crunchy-api, and fastq paths
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    fastq_first = compressed_fastqs["fastq_first_path"]
    # GIVEN a existing spring file
    spring_file = CrunchyAPI.get_spring_path_from_fastq(fastq=fastq_first)
    assert spring_file.exists()
    # GIVEN a existing flag file
    flag_file = CrunchyAPI.get_flag_path(file_path=spring_file)
    assert flag_file.exists()

    # WHEN checking if spring compression is done
    result = crunchy_api.is_spring_compression_done(fastq_first)

    # THEN result should be True
    assert result


def test_is_compression_done_spring_new_files(crunchy_config_dict, compressed_fastqs, caplog):
    """Test if compression is done when fastq files are updated

    This test should fail since the fastq files are new
    """
    caplog.set_level(logging.DEBUG)
    # GIVEN a crunchy-api, and fastq paths
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    fastq_first = compressed_fastqs["fastq_first_path"]
    # GIVEN a existing spring file
    spring_file = CrunchyAPI.get_spring_path_from_fastq(fastq=fastq_first)
    # GIVEN a existing flag file
    flag_file = CrunchyAPI.get_flag_path(file_path=spring_file)
    assert flag_file.exists()

    # GIVEN that the files where updated less than three weeks ago
    crunchy_api.update_metadata_date(flag_file)
    with open(flag_file, "r") as infile:
        content = json.load(infile)
    for file_info in content:
        assert "updated" in file_info

    # WHEN checking if spring compression is done
    result = crunchy_api.is_spring_compression_done(fastq_first)

    # THEN result should be False sinvce the updated date < 3 weeks
    assert result is False
    # THEN assert that correct information is logged
    assert "Fastq files are not old enough" in caplog.text


def test_is_compression_done_spring_old_files(crunchy_config_dict, compressed_fastqs, caplog):
    """Test if compression is done when fastq files are updated bu old

    The function should return true since the files are older than 3 weeks
    """
    caplog.set_level(logging.DEBUG)
    # GIVEN a crunchy-api, and fastq paths
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    fastq_first = compressed_fastqs["fastq_first_path"]
    # GIVEN a existing spring file
    spring_file = CrunchyAPI.get_spring_path_from_fastq(fastq=fastq_first)
    # GIVEN a existing flag file
    flag_file = CrunchyAPI.get_flag_path(file_path=spring_file)
    # GIVEN a date older than three weeks
    old_date = "2019-01-01"
    with open(flag_file, "r") as infile:
        content = json.load(infile)
    # GIVEN that the files where updated more than three weeks ago
    for file_info in content:
        file_info["updated"] = old_date
    with open(flag_file, "w") as outfile:
        outfile.write(json.dumps(content))

    # WHEN checking if spring compression is done
    result = crunchy_api.is_spring_compression_done(fastq_first)

    # THEN result should be True since the files are older than 3 weeks
    assert result is True


def test_get_spring_path_from_fastq():
    """Test to get a spring path"""
    # GIVEN a fastq path for a read 1 in pair
    ind_id = "ind1"
    fastq = Path("".join([ind_id, FASTQ_FIRST_READ_SUFFIX]))

    # WHEN fetching the spring path
    spring_path = CrunchyAPI.get_spring_path_from_fastq(fastq)

    # THEN check that the correct path was returned
    assert spring_path == Path(ind_id).with_suffix(".spring")


def test_get_spring_path_from_second_fastq():
    """Test to get a spring path from second read in pair"""
    # GIVEN a fastq path for a read 2 in pair
    ind_id = "ind1"
    fastq = Path("".join([ind_id, FASTQ_SECOND_READ_SUFFIX]))

    # WHEN fetching the spring path
    spring_path = CrunchyAPI.get_spring_path_from_fastq(fastq)

    # THEN check that the correct path was returned
    assert spring_path == Path(ind_id).with_suffix(".spring")


def test_get_pending_path_from_second_fastq():
    """Test to get a pending path from second read in pair"""
    # GIVEN a fastq path for a read 2 in pair
    ind_id = "ind1"
    fastq = Path("".join([ind_id, FASTQ_SECOND_READ_SUFFIX]))

    # WHEN fetching the spring path
    pending_path = CrunchyAPI.get_pending_path(fastq)

    # THEN check that the correct path was returned
    assert pending_path == Path(ind_id).with_suffix(".crunchy.pending.txt")


def test_get_pending_path_from_spring():
    """Test to get a pending path from a spring path"""
    # GIVEN a spring path
    ind_id = "ind1"
    spring = Path("".join([ind_id, SPRING_SUFFIX]))

    # WHEN fetching the spring path
    pending_path = CrunchyAPI.get_pending_path(spring)

    # THEN check that the correct path was returned
    assert pending_path == Path(ind_id).with_suffix(".crunchy.pending.txt")


def test_is_not_pending(crunchy_config_dict, fastq_paths):
    """test if spring compression is pending"""
    # GIVEN a crunchy-api, and a fastq file
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    fastq_first = fastq_paths["fastq_first_path"]
    # GIVEN a non existing pending flag
    pending_path = crunchy_api.get_pending_path(file_path=fastq_first)
    assert not pending_path.exists()

    # WHEN checking if spring compression is done
    result = crunchy_api.is_compression_pending(fastq_first)

    # THEN result should be False since the pending flag is not there
    assert result is False


def test_is_pending(crunchy_config_dict, compressed_fastqs_pending):
    """test if spring compression is pending"""
    # GIVEN a crunchy-api, and fastq files
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    fastq_first = compressed_fastqs_pending["fastq_first_path"]
    # GIVEN a existing pending flag
    pending_path = crunchy_api.get_pending_path(file_path=fastq_first)
    assert pending_path.exists()

    # WHEN checking if spring compression is pending
    result = crunchy_api.is_compression_pending(fastq_first)

    # THEN result should be True since the pending_path exists
    assert result is True
