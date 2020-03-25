""" Test the osticket app """

import logging

import pytest

from cg.apps.hk import HousekeeperAPI
from cg.exc import TicketCreationError


def test_add_file_with_flat_tag(store_housekeeper, mocker):
    """Test that we can call hk with one tag"""

    # GIVEN an hk api with a mocked store backing it and a string tag
    version_obj = "version_obj"
    file = "file"
    tag = "tag"
    mocker.patch.object(HousekeeperAPI, "new_file")
    mocker.patch.object(HousekeeperAPI, "add_commit")

    # WHEN we call add_file
    new_file = store_housekeeper.add_file(file, version_obj, tag)

    # THEN the file should have been added to hk
    assert new_file


def test_add_file_with_list_of_tags(store_housekeeper, mocker):
    """Test that we can call hk with one tag"""

    # GIVEN an hk api with a mocked store backing it and a string tag
    version_obj = "version_obj"
    file = "file"
    tag = ["tag1", "tag2"]
    mocker.patch.object(HousekeeperAPI, "new_file")
    mocker.patch.object(HousekeeperAPI, "add_commit")

    # WHEN we call add_file
    new_file = store_housekeeper.add_file(file, version_obj, tag)

    # THEN the file should have been added to hk
    assert new_file
