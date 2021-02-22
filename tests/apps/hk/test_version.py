"""Test how the api handles versions"""


def test_new_version(a_date, housekeeper_api):
    """Test to create a new version with the api"""
    # GIVEN a housekeeper api and a date
    # WHEN creating a version object
    version_obj = housekeeper_api.new_version(created_at=a_date)
    # THEN assert that the version obj was created
    assert version_obj
    # THEN assert that the version object has the correct date
    assert version_obj.created_at == a_date
    # THEN assert that the other members are set to None
    assert version_obj.expires_at is None
    assert version_obj.included_at is None
    assert version_obj.archived_at is None
    assert version_obj.archive_path is None
    # THEN assert that there is no bundle id
    assert version_obj.bundle_id is None


def test_get_version_non_existing(housekeeper_api, a_date):
    """Test to get a version when there are no existing version"""
    # GIVEN a empty housekeeper_api
    # WHEN fetching a version
    version_obj = housekeeper_api.version(bundle=None, date=a_date)
    # THEN assert that the function returns None
    assert version_obj is None


def test_get_version_existing(housekeeper_api, a_date, bundle_data):
    """Test to get a version when there is a bundle and a version"""
    # GIVEN a populated housekeeper_api
    bundle_obj, version_obj = housekeeper_api.add_bundle(bundle_data)
    housekeeper_api.add_commit(bundle_obj, version_obj)
    # WHEN fetching a version
    fetched_version = housekeeper_api.version(bundle=bundle_obj.name, date=a_date)
    # THEN assert that the function returns True and that version has a bundle_id attribute
    assert fetched_version
    assert fetched_version.bundle_id == bundle_obj.id


def test_add_version_existing_bundle(populated_housekeeper_api, later_date, case_id, small_helpers):
    """Test to get a version when there is a bundle and a version"""
    # GIVEN a populated housekeeper_api and a bundle with one version
    bundle_obj = populated_housekeeper_api.bundle(name=case_id)
    assert bundle_obj
    assert small_helpers.length_of_iterable(bundle_obj.versions) == 1
    # WHEN creating a newer version and adding it to the bundle
    new_version = populated_housekeeper_api.new_version(created_at=later_date)
    new_version.bundle = bundle_obj
    populated_housekeeper_api.add_commit(new_version)

    # THEN assert that the bundle has two versions
    bundle_obj = populated_housekeeper_api.bundle(name=case_id)
    assert small_helpers.length_of_iterable(bundle_obj.versions) == 2


def test_get_last_version(populated_housekeeper_api, later_date, case_id):
    """Test to get a version when there is a bundle and a version"""
    # GIVEN a populated housekeeper_api and a bundle with two versions
    bundle_obj = populated_housekeeper_api.bundle(name=case_id)
    new_version = populated_housekeeper_api.new_version(created_at=later_date)
    new_version.bundle = bundle_obj
    populated_housekeeper_api.add_commit(new_version)

    # WHEN fetching the last version of a bundle
    fetched_version = populated_housekeeper_api.last_version(bundle=case_id)

    # THEN assert that the later_date version is fetched
    assert fetched_version.created_at == later_date
