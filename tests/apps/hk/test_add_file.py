""" Test the Housekeeper app """

from cg.apps.hk import HousekeeperAPI


def test_add_file_with_list_of_tags(store_housekeeper, mocker):
    """Test that we can call hk with one tag"""

    # GIVEN an hk api with a mocked store backing it and a string tag
    version_obj = "version_obj"
    file = "file"
    tags = ["tag1", "tag2"]
    mocker.patch.object(HousekeeperAPI, "new_file")
    mocker.patch.object(HousekeeperAPI, "add_commit")

    # WHEN we call add_file
    new_file = store_housekeeper.add_file(file, version_obj, tags)

    # THEN the file should have been added to hk
    assert new_file
