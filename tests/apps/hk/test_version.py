"""Test how the api handles versions."""
from typing import Dict, Any

import datetime

from tests.mocks.hk_mock import MockHousekeeperAPI
from tests.small_helpers import SmallHelpers


def test_new_version(housekeeper_api: MockHousekeeperAPI, timestamp: datetime.datetime):
    """Test to create a new version with the API."""
    # GIVEN a housekeeper api and a date

    # WHEN creating a version object
    version_obj = housekeeper_api.new_version(created_at=timestamp)

    # THEN assert that the version obj was created
    assert version_obj

    # THEN assert that the version object has the correct date
    assert version_obj.created_at == timestamp

    # THEN assert that the other members are set to None
    for member in [
        version_obj.expires_at,
        version_obj.included_at,
        version_obj.archived_at,
        version_obj.archive_path,
    ]:
        assert member is None

    # THEN assert that there is no bundle id
    assert version_obj.bundle_id is None


def test_get_version_non_existing(
    housekeeper_api: MockHousekeeperAPI, timestamp: datetime.datetime
):
    """Test to get a version when there are no existing version."""
    # GIVEN a empty housekeeper_api

    # WHEN fetching a version
    version_obj = housekeeper_api.version(bundle=None, date=timestamp)

    # THEN assert that the function returns None
    assert version_obj is None


def test_get_version_existing(
    housekeeper_api: MockHousekeeperAPI,
    timestamp: datetime.datetime,
    hk_bundle_data: Dict[str, Any],
):
    """Test to get a version when there is a bundle and a version."""
    # GIVEN a populated housekeeper_api
    bundle_obj, version_obj = housekeeper_api.add_bundle(hk_bundle_data)
    housekeeper_api.add_commit(bundle_obj)
    housekeeper_api.add_commit(version_obj)

    # WHEN fetching a version
    fetched_version = housekeeper_api.version(bundle=bundle_obj.name, date=timestamp)

    # THEN assert that the function returns True
    assert fetched_version

    # THEN assert version has a bundle_id attribute
    assert fetched_version.bundle_id == bundle_obj.id


def test_add_version_existing_bundle(
    populated_housekeeper_api: MockHousekeeperAPI,
    later_timestamp: datetime.datetime,
    case_id: str,
    small_helpers: SmallHelpers,
):
    """Test to get a version when there is a bundle and a version."""
    # GIVEN a populated housekeeper_api and a bundle with one version
    bundle_obj = populated_housekeeper_api.bundle(name=case_id)
    assert bundle_obj
    assert small_helpers.length_of_iterable(bundle_obj.versions) == 1

    # WHEN creating a newer version and adding it to the bundle
    new_version = populated_housekeeper_api.new_version(created_at=later_timestamp)
    new_version.bundle = bundle_obj
    populated_housekeeper_api.add_commit(new_version)

    # THEN assert that the bundle has two versions
    bundle_obj = populated_housekeeper_api.bundle(name=case_id)
    assert small_helpers.length_of_iterable(bundle_obj.versions) == 2


def test_get_last_version(
    case_id: str, populated_housekeeper_api: MockHousekeeperAPI, later_timestamp: datetime.datetime
):
    """Test to get a version when there is a bundle and a version."""
    # GIVEN a populated housekeeper_api and a bundle with two versions
    bundle_obj = populated_housekeeper_api.bundle(name=case_id)
    new_version = populated_housekeeper_api.new_version(created_at=later_timestamp)
    new_version.bundle = bundle_obj
    populated_housekeeper_api.add_commit(new_version)

    # WHEN fetching the last version of a bundle
    fetched_version = populated_housekeeper_api.last_version(bundle=case_id)

    # THEN assert that the later_date version is fetched
    assert fetched_version.created_at == later_timestamp


def test_get_latest_bundle_version_no_housekeeper_bundle(
    case_id: str, housekeeper_api: MockHousekeeperAPI, caplog
):
    """Test get_latest_bundle_version function when there is no case bundle in Housekeeper."""

    # GIVEN a case id

    # WHEN getting the version_obj
    res = housekeeper_api.get_latest_bundle_version(bundle_name=case_id)

    # THEN assert that None was returned since there is no such case bundle in Housekeeper
    assert res is None

    # THEN assert that no bundle is found
    assert f"No bundle found for {case_id} in Housekeeper" in caplog.text


def test_get_latest_bundle_version_with_housekeeper_bundle(
    populated_housekeeper_api: MockHousekeeperAPI, later_timestamp: datetime.datetime, case_id: str
):
    """Test to get a version when there is a bundle and a version."""
    # GIVEN a populated housekeeper_api
    bundle_obj = populated_housekeeper_api.bundle(name=case_id)

    # GIVEN a bundle with two versions
    new_version = populated_housekeeper_api.new_version(created_at=later_timestamp)
    new_version.bundle = bundle_obj
    populated_housekeeper_api.add_commit(new_version)

    # WHEN fetching the last version of a bundle
    fetched_version = populated_housekeeper_api.get_latest_bundle_version(bundle_name=case_id)

    # THEN assert that the later_date version was fetched
    assert fetched_version.created_at == later_timestamp


def test_get_create_version(
    another_case_id: str,
    populated_housekeeper_api: MockHousekeeperAPI,
    case_id: str,
):
    # Given a populated housekeeper_api with a bundle
    version_obj = populated_housekeeper_api.bundle(case_id).versions[0]

    # When the case_id is given the function should return its latest version
    latest_version = populated_housekeeper_api.get_create_version(case_id)

    # Then assert that the versions match
    assert version_obj == latest_version

    # When a case_id not present in hk is given.
    latest_version = populated_housekeeper_api.get_create_version(another_case_id)

    # Then assert the new bundle is created the version is new.
    assert latest_version.bundle.name == another_case_id
