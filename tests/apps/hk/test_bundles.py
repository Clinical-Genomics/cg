"""Test how the api handles bundles"""
from datetime import datetime


def test_new_bundle(housekeeper_api, small_helpers):
    """Test to create a bundle with the housekeeper api"""
    # GIVEN a housekeeper api without bundles
    assert small_helpers.length_of_iterable(housekeeper_api.bundles()) == 0
    # GIVEN some bundle information
    bundle_name = "a bundle"
    created = datetime.now()
    # WHEN creating a new bundle
    bundle_obj = housekeeper_api.new_bundle(name=bundle_name, created_at=created)

    # THEN assert that the bundle object got the correct name
    assert bundle_obj.name == bundle_name
    # THEN assert that no bundle was added to the database
    assert small_helpers.length_of_iterable(housekeeper_api.bundles()) == 0


def test_add_bundle(housekeeper_api, bed_file, small_helpers):
    """Test to add a housekeeper bundle"""
    # GIVEN a empty housekeeper api
    assert small_helpers.length_of_iterable(housekeeper_api.bundles()) == 0
    # GIVEN some bundle information
    bundle_name = "a bundle"
    created = datetime.now()
    bundle_data = {
        "name": bundle_name,
        "created": created,
        "files": [{"path": bed_file, "archive": False, "tags": ["bed"]}],
    }
    # WHEN adding the bundle
    bundle_obj, _ = housekeeper_api.add_bundle(bundle_data)

    # THEN assert that no bundle was added to the database
    assert small_helpers.length_of_iterable(housekeeper_api.bundles()) == 0
    # THEN assert that the bundle object got the correct name
    assert bundle_obj.name == bundle_name


def test_add_bundle_and_commit(housekeeper_api, minimal_bundle_obj, small_helpers):
    """Test to add a housekeeper bundle and make it persistent"""
    # GIVEN a empty housekeeper api and a bundle object
    assert small_helpers.length_of_iterable(housekeeper_api.bundles()) == 0

    # WHEN commiting the bundle
    housekeeper_api.add_commit(minimal_bundle_obj)

    # THEN assert that a bundle was added to the database
    assert small_helpers.length_of_iterable(housekeeper_api.bundles()) == 1


def test_get_bundle(housekeeper_api, minimal_bundle_obj):
    """Test to add a housekeeper bundle and fetch it back"""
    # GIVEN a housekeeper api with a bundle object
    bundle_name = minimal_bundle_obj.name
    assert housekeeper_api.bundle(bundle_name) is None
    housekeeper_api.add_commit(minimal_bundle_obj)

    # WHEN fetching the bundle
    bundle_obj = housekeeper_api.bundle(bundle_name)

    # THEN assert that a bundle was fetched
    assert bundle_obj
    assert bundle_obj.name == bundle_name
