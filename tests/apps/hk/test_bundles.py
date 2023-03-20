"""Test how the api handles bundles."""
from typing import Dict, Any

from datetime import datetime

from tests.mocks.hk_mock import MockHousekeeperAPI
from tests.small_helpers import SmallHelpers

from housekeeper.store.models import Bundle


def test_new_bundle(
    case_id: str,
    housekeeper_api: MockHousekeeperAPI,
    small_helpers: SmallHelpers,
    timestamp_now: datetime,
):
    """Test to create a bundle with the Housekeeper API."""
    # GIVEN a Housekeeper API without bundles
    assert small_helpers.length_of_iterable(housekeeper_api.bundles()) == 0

    # GIVEN some bundle information

    # WHEN creating a new bundle
    bundle_obj = housekeeper_api.new_bundle(name=case_id, created_at=timestamp_now)

    # THEN assert that the bundle object got the correct name
    assert bundle_obj.name == case_id
    # THEN assert that no bundle was added to the database
    assert small_helpers.length_of_iterable(housekeeper_api.bundles()) == 0


def test_add_bundle(
    hk_bundle_data: Dict[str, Any],
    case_id: str,
    housekeeper_api: MockHousekeeperAPI,
    small_helpers: SmallHelpers,
):
    """Test to add a Housekeeper bundle."""
    # GIVEN a empty housekeeper api
    assert small_helpers.length_of_iterable(housekeeper_api.bundles()) == 0
    # GIVEN some bundle information

    # WHEN adding the bundle
    bundle_obj, _ = housekeeper_api.add_bundle(hk_bundle_data)

    # THEN assert that no bundle was added to the database
    assert small_helpers.length_of_iterable(housekeeper_api.bundles()) == 0
    # THEN assert that the bundle object got the correct name
    assert bundle_obj.name == case_id


def test_add_bundle_and_commit(
    housekeeper_api: MockHousekeeperAPI, minimal_bundle_obj, small_helpers: SmallHelpers
):
    """Test to add a housekeeper bundle and make it persistent."""
    # GIVEN a empty housekeeper api and a bundle object
    assert small_helpers.length_of_iterable(housekeeper_api.bundles()) == 0

    # WHEN committing the bundle
    housekeeper_api.add_commit(minimal_bundle_obj)

    # THEN assert that a bundle was added to the database
    assert small_helpers.length_of_iterable(housekeeper_api.bundles()) == 1


def test_get_bundle(housekeeper_api: MockHousekeeperAPI, minimal_bundle_obj: Bundle):
    """Test to add a housekeeper bundle and fetch it back."""
    # GIVEN a housekeeper api with a bundle object
    assert housekeeper_api.bundle(minimal_bundle_obj.name) is None
    housekeeper_api.add_commit(minimal_bundle_obj)

    # WHEN fetching the bundle
    bundle_obj = housekeeper_api.bundle(minimal_bundle_obj.name)

    # THEN assert that a bundle was fetched
    assert bundle_obj
    assert bundle_obj.name == minimal_bundle_obj.name


def test_create_bundle_and_version(
    case_id: str,
    housekeeper_api: MockHousekeeperAPI,
    minimal_bundle_obj: Bundle,
    small_helpers: SmallHelpers,
):
    """Test to create a housekeeper bundle and version."""

    # GIVEN a housekeeper api without bundles
    assert small_helpers.length_of_iterable(housekeeper_api.bundles()) == 0

    # GIVEN a bundle name

    # WHEN creating a new bundle and version
    bundle_obj = housekeeper_api.create_new_bundle_and_version(name=case_id)

    # THEN a new bundle with the correct name is created, with a version, and added to the database
    assert housekeeper_api.bundle(case_id) is not None
    assert bundle_obj.name == case_id
    assert bundle_obj.versions is not None
    assert small_helpers.length_of_iterable(housekeeper_api.bundles()) == 1
