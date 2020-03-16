import pytest
import os
from pathlib import Path

from cg.apps.scoutapi import ScoutAPI
from cg.apps.hk import HousekeeperAPI
from cg.apps.crunchy import CrunchyAPI
from cg.meta.compress import CompressAPI


def test_get_nlinks(compress_api, compress_test_dir):
    """Test get_nlinks"""
    # GIVEN a bam
    file_path = compress_test_dir / "file"
    file_path.touch()

    # WHEN getting number of links to inode
    nlinks = compress_api.get_nlinks(file_link=file_path)

    # THEN number of links should be one
    assert nlinks == 1

    # WHEN adding a link
    first_link = compress_test_dir / "link-1"
    os.link(file_path, first_link)
    nlinks = compress_api.get_nlinks(file_link=file_path)

    # THEN number of links should be two
    assert nlinks == 2

    # WHEN adding yet another link
    second_link = compress_test_dir / "link-2"
    os.link(file_path, second_link)
    nlinks = compress_api.get_nlinks(file_link=file_path)

    # THEN number of links should be three
    assert nlinks == 3


def test_get_bam_files(compress_api, compress_scout_case, bam_files_hk_list, mocker):
    """test get_bam_files method"""

    # GIVEN a case id
    case_id = "test_case"
    mock_get_cases = mocker.patch.object(
        ScoutAPI, "get_cases", return_value=[compress_scout_case]
    )
    mock_get_files = mocker.patch.object(
        HousekeeperAPI, "get_files", return_value=bam_files_hk_list
    )

    # WHEN getting bam-files
    bam_dict = compress_api.get_bam_files(case_id=case_id)

    # THEN the bam-files for the samples will be in the dictionary
    assert set(bam_dict.keys()) == set(["sample_1", "sample_2", "sample_3"])


def test_compress_case(compress_api, bam_dict, mocker):
    """Test compress_case method"""
    # GIVEN a compress api and a bam dictionary
    mock_bam_to_cram = mocker.patch.object(CrunchyAPI, "bam_to_cram")

    # WHEN compressing the case
    compress_api.compress_case(bam_dict=bam_dict)

    # THEN all samples in bam-files will have been compressed
    assert mock_bam_to_cram.call_count == len(bam_dict)


def test_update_scout(compress_api, bam_dict, mock_compress_func, mocker):
    """ Test update_hk method"""
    mock_compress_func(bam_dict)
    mock_get_bam_files = mocker.patch.object(
        CompressAPI, "get_bam_files", return_value=bam_dict
    )
    mock_update_alignment_file = mocker.patch.object(ScoutAPI, "update_alignment_file")
    # GIVEN a case-id
    case_id = "test_case"

    # WHEN updating scout
    compress_api.update_scout(case_id=case_id)

    # THEN update_alignment_file should have been callen three times
    assert mock_update_alignment_file.call_count == len(bam_dict)


def test_update_hk(compress_api, bam_dict, mock_compress_func, mocker):
    """ Test update_hk method"""
    mock_compress_func(bam_dict)
    mock_get_bam_files = mocker.patch.object(
        CompressAPI, "get_bam_files", return_value=bam_dict
    )
    mock_add_file_with_tags = mocker.patch.object(HousekeeperAPI, "add_file_with_tags")
    # GIVEN a case-id and a compress api
    case_id = "test-case"

    # WHEN updating hk
    compress_api.update_hk(case_id=case_id)

    # THEN add_file_with_tags should have been called 6 times (two for every case)
    assert mock_add_file_with_tags.call_count == 6


def test_remove_bams(compress_api, bam_dict, mock_compress_func, mocker):
    """ Test remove_bams method"""
    # GIVEN a bam-dict and a compress api
    compressed_dict = mock_compress_func(bam_dict)

    for sample, files in compressed_dict.items():
        assert Path(files["bam"].full_path).exists()
        assert Path(files["bai"].full_path).exists()
        assert Path(files["cram"].full_path).exists()
        assert Path(files["crai"].full_path).exists()
        assert Path(files["flag"].full_path).exists()

    mock_get_bam_files = mocker.patch.object(
        CompressAPI, "get_bam_files", return_value=bam_dict
    )

    # WHEN calling remove_bams
    compress_api.remove_bams(case_id="test-case")

    # THEN the bam-files and flag-file should not exist

    for sample, files in compressed_dict.items():
        assert not Path(files["bam"].full_path).exists()
        assert not Path(files["bai"].full_path).exists()
        assert Path(files["cram"].full_path).exists()
        assert Path(files["crai"].full_path).exists()
        assert not Path(files["flag"].full_path).exists()
