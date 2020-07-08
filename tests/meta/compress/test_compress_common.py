""" Tests for common functions of the compress API """
import os

from cg.meta.compress import files


def test_get_nlinks_one_link(project_dir):
    """Test get_nlinks when there is one link to a file"""
    # GIVEN a file with one link
    file_path = project_dir / "file"
    file_path.touch()

    # WHEN getting number of links to inode
    nlinks = files.get_nlinks(file_link=file_path)

    # THEN number of links should be one
    assert nlinks == 1


def test_get_nlinks_two_links(project_dir):
    """Test get_nlinks two links"""
    # GIVEN a file with two links
    file_path = project_dir / "file"
    file_path.touch()

    first_link = project_dir / "link-1"
    os.link(file_path, first_link)

    # WHEN fetching the number of links from the API
    nlinks = files.get_nlinks(file_link=file_path)

    # THEN number of links should be two
    assert nlinks == 2

    # WHEN adding yet another link
    second_link = project_dir / "link-2"
    os.link(file_path, second_link)
    nlinks = files.get_nlinks(file_link=file_path)

    # THEN number of links should be three
    assert nlinks == 3


def test_get_nlinks_three_links(project_dir):
    """Test get_nlinks when three links"""
    # GIVEN a file with two links
    file_path = project_dir / "file"
    file_path.touch()

    first_link = project_dir / "link-1"
    os.link(file_path, first_link)

    second_link = project_dir / "link-2"
    os.link(file_path, second_link)

    # WHEN fetching the links from the api
    nlinks = files.get_nlinks(file_link=file_path)

    # THEN number of links should be three
    assert nlinks == 3


def test_get_scout_case_no_scout_case(compress_api, case_id, caplog):
    """test get_bam_dict method when there is not case in scout"""

    # GIVEN a case id

    # WHEN getting bam-files
    res = compress_api.get_scout_case(case_id=case_id)

    # THEN assert that None was returned since the case was not found in scout
    assert res is None
    # THEN assert that the correct information is being processed
    assert f"{case_id} not found in scout" in caplog.text


def test_get_latest_version_no_housekeeper_files(compress_api, compress_scout_case, caplog):
    """test get_bam_dict method when there is not case in scout"""

    case_id = compress_scout_case
    # GIVEN a case id

    # WHEN getting the version_obj
    res = compress_api.get_latest_version(case_id)

    # THEN assert that None was returned since the case was not found in scout
    assert res is None
    # THEN assert that the correct information is being processed
    assert f"No bundle found for {case_id} in housekeeper" in caplog.text
