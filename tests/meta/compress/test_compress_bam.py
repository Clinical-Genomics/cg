"""Tests for bam part of meta compress api"""
import logging
import os
from pathlib import Path


def test_get_bam_files(compress_api, compress_scout_case, compress_hk_bam_bundle, case_id, helpers):
    """test get_bam_files method"""

    # GIVEN a scout api that returns some case info
    scout_api = compress_api.scout_api
    scout_api.add_mock_case(compress_scout_case)
    # GIVEN a hk api that returns some data
    hk_api = compress_api.hk_api
    helpers.ensure_hk_bundle(hk_api, compress_hk_bam_bundle)

    # WHEN getting bam-files
    bam_dict = compress_api.get_bam_files(case_id=case_id)

    # THEN the bam-files for the samples will be in the dictionary
    assert set(bam_dict.keys()) == set(["sample_1", "sample_2", "sample_3"])


def test_get_bam_files_no_scout_case(compress_api, case_id, caplog):
    """test get_bam_files method when there is not case in scout"""

    # GIVEN a case id

    # WHEN getting bam-files
    bam_dict = compress_api.get_bam_files(case_id=case_id)

    # THEN assert that None was returned since the case was not found in scout
    assert bam_dict is None
    # THEN assert that the correct information is being processed
    assert f"{case_id} not found in scout" in caplog.text


def test_get_bam_files_no_housekeeper_files(compress_api, compress_scout_case, caplog):
    """test get_bam_files method when there is not case in scout"""

    case_id = compress_scout_case
    # GIVEN a scout api that returns some case info
    scout_api = compress_api.scout_api
    scout_api.add_mock_case(case_id)
    # GIVEN a case id

    # WHEN getting bam-files
    bam_dict = compress_api.get_bam_files(case_id=case_id)

    # THEN assert that None was returned since the case was not found in scout
    assert bam_dict is None
    # THEN assert that the correct information is being processed
    assert f"No files found in latest housekeeper version for {case_id}" in caplog.text


def test_check_bam_path(compress_api, bam_file):
    """Test the check bam file with an existing bam file"""
    # GIVEN an existing bam_path
    assert bam_file.exists()

    # WHEN checking the bam path in string format
    res = compress_api.get_bam_path(str(bam_file), hk_files=[bam_file])

    # THEN assert that the file is returned as a path object
    assert res == bam_file


def test_get_bam_path_multiple_links(compress_api, multi_linked_file, caplog):
    """Test to get the bam path when file have multiple links"""
    # GIVEN an file with multiple links
    assert os.stat(multi_linked_file).st_nlink > 1

    # WHEN checking the bam path in string format
    res = compress_api.get_bam_path(str(multi_linked_file), hk_files=[multi_linked_file])

    # THEN assert that the file is returned as a path object
    assert res is None
    # THEN assert that the correct information is being processed
    assert "has more than 1 links to same inode" in caplog.text


def test_check_bam_path_not_in_hk(compress_api, bam_file, caplog):
    """Test the get the bam path when it is not in the hk files"""
    # GIVEN an existing bam_path
    assert bam_file.exists()

    # WHEN checking the bam path in string format but not in hk_files
    res = compress_api.get_bam_path(str(bam_file), hk_files=[])

    # THEN assert that None is returned
    assert res is None
    # THEN assert that the correct information is being processed
    assert f"{bam_file} not in latest version of housekeeper bundle" in caplog.text


def test_check_bam_file_wrong_suffix(compress_api, bai_file, caplog):
    """Test the check bam file when the suffix is wrong"""
    # GIVEN an existing file that is not a bam file (not ends with .bam)
    assert bai_file.exists()

    # WHEN checking the bam path in string format
    res = compress_api.get_bam_path(str(bai_file), hk_files=[bai_file])

    # THEN assert that None is returned
    assert res is None
    # THEN assert that the correct information is being communicated
    assert f"Alignment file does not have correct suffix .bam" in caplog.text


def test_check_bam_file_no_file(compress_api, caplog):
    """Test the check bam file without None as argument"""
    # GIVEN a compress api

    # WHEN getting the bam path with None
    res = compress_api.get_bam_path(None, hk_files=[])

    # THEN assert that the file is returned as a path object
    assert res is None
    # THEN assert that the correct information is being communicated
    assert f"No bam file found" in caplog.text


def test_check_bam_file_non_existing(compress_api, bam_path):
    """Test the check bam file with a non existing bam file"""
    # GIVEN a non existing bam_path
    assert not bam_path.exists()

    # WHEN checking the bam path in string format
    res = compress_api.get_bam_path(str(bam_path), hk_files=[bam_path])

    # THEN assert that None is returned
    assert res is None


def test_compress_case_bam(populated_compress_api, case_id, caplog):
    """Test to compress all bam files for a case"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a populated compress api

    # WHEN Compressing the bam files for the case
    res = populated_compress_api.compress_case_bam(case_id)

    # THEN assert compression succeded
    assert res is True
    # THEN assert that the correct information is communicated
    assert "Compressing" in caplog.text


def test_compress_case_bam_compression_not_possible(
    populated_compress_api, compress_hk_bam_bundle, case_id, caplog
):
    """Test to compress all bam files for a case when compression is not possible for one sample"""
    caplog.set_level(logging.DEBUG)
    # GIVEN an existing bam file
    for file_info in compress_hk_bam_bundle["files"]:
        if "bam" in file_info["tags"]:
            bam_path = Path(file_info["path"])
    assert bam_path.exists()
    # GIVEN a that compression is not possible for one sample
    populated_compress_api.crunchy_api.set_compression_not_possible(bam_path)

    # WHEN Compressing the bam files for the case
    res = populated_compress_api.compress_case_bam(case_id)

    # THEN assert compression succeded
    assert res is False
    # THEN assert that the correct information is communicated
    assert "BAM to CRAM compression not possible" in caplog.text


def test_compress_case_bam_no_scout_case(compress_api, compress_hk_bam_bundle, helpers, caplog):
    """Test to compress the bam files of a case when the scout does not exist in scout"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a scout api that have no cases
    case_id = compress_hk_bam_bundle["name"]
    scout_api = compress_api.scout_api
    assert not scout_api.get_cases(case_id)
    # GIVEN a hk api that returns some data
    hk_api = compress_api.hk_api
    helpers.ensure_hk_bundle(hk_api, compress_hk_bam_bundle)

    # WHEN Compressing the bam files for the case
    res = compress_api.compress_case_bam(case_id)

    # THEN assert compression could not complete
    assert res is False
    # THEN assert that the correct information is communicated
    assert f"{case_id} not found in scout" in caplog.text
