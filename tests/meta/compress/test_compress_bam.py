"""Tests for bam part of meta compress api"""
import os
from pathlib import Path

from cg.apps.crunchy import CrunchyAPI
from cg.apps.scoutapi import ScoutAPI


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


def test_compress_case_bams(compress_api, bam_dict, mocker):
    """Test compress_case method"""
    # GIVEN a compress api and a bam dictionary
    mock_bam_to_cram = mocker.patch.object(CrunchyAPI, "bam_to_cram")

    # WHEN compressing the case
    compress_api.compress_case_bams(bam_dict=bam_dict)

    # THEN all samples in bam-files will have been compressed
    assert mock_bam_to_cram.call_count == len(bam_dict)


def test_remove_bams(compress_api, bam_dict, mock_compress_func):
    """ Test remove_bams method"""
    # GIVEN a bam-dict and a compress api
    compressed_dict = mock_compress_func(bam_dict)

    for _, files in compressed_dict.items():
        assert Path(files["bam"].full_path).exists()
        assert Path(files["bai"].full_path).exists()
        assert Path(files["cram"].full_path).exists()
        assert Path(files["crai"].full_path).exists()
        assert Path(files["flag"].full_path).exists()

    # WHEN calling remove_bams
    compress_api.remove_bams(bam_dict=bam_dict)

    # THEN the bam-files and flag-file should not exist

    for sample_id in compressed_dict:
        files = compressed_dict[sample_id]
        assert not Path(files["bam"].full_path).exists()
        assert not Path(files["bai"].full_path).exists()
        assert Path(files["cram"].full_path).exists()
        assert Path(files["crai"].full_path).exists()
        assert not Path(files["flag"].full_path).exists()
