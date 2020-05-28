""" Test adding files with housekeeper api """


def test_add_file_with_flat_tag(housekeeper_api, helpers, hk_bundle_data, microbial_orderform):
    """Test that we can call hk with one existing tag"""

    # GIVEN an hk api populated with a version obj
    version_obj = helpers.ensure_hk_version(housekeeper_api, hk_bundle_data)
    # GIVEN a tag that is just a string that exists
    tag_name = "bed"
    assert housekeeper_api.tag(tag_name)

    # WHEN we call add_file
    new_file = housekeeper_api.add_file(microbial_orderform, version_obj, tag_name)

    # THEN the file should have been added to hk
    assert new_file


def test_add_file_with_list_of_tags(housekeeper_api, helpers, hk_bundle_data, microbial_orderform):
    """Test that we can call hk with more than one tags"""

    # GIVEN an hk api populated with a version obj
    version_obj = helpers.ensure_hk_version(housekeeper_api, hk_bundle_data)
    # GIVEN a list of tags that does not exist
    tags = ["missing_tag_1", "missing_tag_2"]
    for tag_name in tags:
        assert housekeeper_api.tag(tag_name) is None

    # WHEN we call add_file
    new_file = housekeeper_api.add_file(microbial_orderform, version_obj, tags)

    # THEN the file should have been added to hk
    assert new_file
