import pytest
import os
from pathlib import Path

from cg.apps.scoutapi import ScoutAPI
from cg.apps.hk import HousekeeperAPI
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

    case_id = "test_case"
    mock_get_cases = mocker.patch.object(
        ScoutAPI, "get_cases", return_value=[compress_scout_case]
    )
    mock_get_files = mocker.patch.object(
        HousekeeperAPI, "get_files", return_value=bam_files_hk_list
    )
    bam_dict = compress_api.get_bam_files(case_id=case_id)
    assert set(bam_dict.keys()) == set(["sample_1", "sample_2", "sample_3"])
