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
