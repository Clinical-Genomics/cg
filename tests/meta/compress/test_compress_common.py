""" Tests for common functions of the compress API """

import os


def test_get_nlinks_one_link(compress_api, project_dir):
    """Test get_nlinks when there is one link to a file"""
    # GIVEN a file with one link
    file_path = project_dir / "file"
    file_path.touch()

    # WHEN getting number of links to inode
    nlinks = compress_api.get_nlinks(file_link=file_path)

    # THEN number of links should be one
    assert nlinks == 1


def test_get_nlinks_two_links(compress_api, project_dir):
    """Test get_nlinks two links"""
    # GIVEN a file with two links
    file_path = project_dir / "file"
    file_path.touch()

    first_link = project_dir / "link-1"
    os.link(file_path, first_link)

    # WHEN fetching the number of links from the API
    nlinks = compress_api.get_nlinks(file_link=file_path)

    # THEN number of links should be two
    assert nlinks == 2

    # WHEN adding yet another link
    second_link = project_dir / "link-2"
    os.link(file_path, second_link)
    nlinks = compress_api.get_nlinks(file_link=file_path)

    # THEN number of links should be three
    assert nlinks == 3


def test_get_nlinks_three_links(compress_api, project_dir):
    """Test get_nlinks when three links"""
    # GIVEN a file with two links
    file_path = project_dir / "file"
    file_path.touch()

    first_link = project_dir / "link-1"
    os.link(file_path, first_link)

    second_link = project_dir / "link-2"
    os.link(file_path, second_link)

    # WHEN fetching the links from the api
    nlinks = compress_api.get_nlinks(file_link=file_path)

    # THEN number of links should be three
    assert nlinks == 3


def test_update_scout(compress_api, bam_dict, mock_compress_func):
    """ Test to update the bam paths in scout"""
    mock_compress_func(bam_dict)
    scout_api = compress_api.scout_api
    # GIVEN a case-id
    case_id = "test_case"

    # WHEN updating the bam paths in scout
    compress_api.update_scout(case_id=case_id, bam_dict=bam_dict)

    # THEN update_alignment_file should have been callen three times
    assert scout_api.nr_alignment_updates() == len(bam_dict)


def test_update_hk(compress_api, bam_dict, mock_compress_func):
    """ Test to update the bam paths in housekeeper"""
    mock_compress_func(bam_dict)
    hk_api = compress_api.hk_api
    # GIVEN a empty hk api
    assert len(hk_api.files()) == 0
    # GIVEN a case-id and a compress api
    case_id = "test-case"

    # WHEN updating hk
    compress_api.update_hk(case_id=case_id, bam_dict=bam_dict)

    # THEN add_file should have been called 6 times (two for every case)
    assert len(hk_api.files()) == 6
