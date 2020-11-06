"""Tests for the compress data class"""
import os
from pathlib import Path
from datetime import datetime

from cg.models import CompressionData


def test_get_run_name():
    """Test that the correct run name is returned"""
    # GIVEN a file path that ends with a run name
    file_path = Path("/path/to/dir")
    run_name = "a_run"
    # GIVEN a compression data object
    compression_obj = CompressionData(file_path / run_name)

    # WHEN fetching the run name
    # THEN assert the correct run name is returned
    assert compression_obj.run_name == run_name


def test_get_change_date(compression_object):
    """Test to get the date time for when a file was changed"""
    # GIVEN a existing file
    file_path = compression_object.spring_path
    file_path.touch()

    # WHEN fetching the date when file was created
    change_date = compression_object.get_change_date(file_path)

    # THEN check that it is the same date as today
    assert change_date.date() == datetime.today().date()


def test_get_nlinks_one_link(compression_object):
    """Test get_nlinks when there is one link to a file"""
    # GIVEN a file with one link
    file_path = compression_object.spring_path
    file_path.touch()

    # WHEN getting number of links to inode
    nlinks = compression_object.get_nlinks(file_path)

    # THEN number of links should be one
    assert nlinks == 1


def test_get_nlinks_two_links(compression_object):
    """Test get_nlinks two links"""
    # GIVEN a file with two links
    file_path = compression_object.spring_path
    file_path.touch()

    first_link = file_path.parent / "link-1"
    os.link(file_path, first_link)

    # WHEN fetching the number of links from the API
    nlinks = compression_object.get_nlinks(file_path)

    # THEN number of links should be two
    assert nlinks == 2


def test_get_nlinks_three_links(compression_object):
    """Test get_nlinks when three links"""
    # GIVEN a file with two links
    file_path = compression_object.spring_path
    file_path.touch()

    first_link = file_path.parent / "link-1"
    os.link(file_path, first_link)

    second_link = file_path.parent / "link-2"
    os.link(file_path, second_link)

    # WHEN fetching the links from the api
    nlinks = compression_object.get_nlinks(file_path)

    # THEN number of links should be three
    assert nlinks == 3
