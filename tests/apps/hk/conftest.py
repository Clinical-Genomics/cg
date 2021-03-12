"""Fixtures for the housekeeper tests"""

import datetime

import pytest

from cg.apps.housekeeper.hk import HousekeeperAPI
from housekeeper.store import models


@pytest.fixture(name="hk_config")
def fixture_hk_config(root_path) -> dict:
    """Return a dictionary with housekeeper api configs for testing"""
    config = {"housekeeper": {"database": "sqlite:///:memory:", "root": str(root_path)}}
    return config


@pytest.fixture(scope="function", name="housekeeper_api")
def fixture_housekeeper_api(hk_config):
    """Setup Housekeeper store."""
    _api = HousekeeperAPI(hk_config)
    _api.initialise_db()
    yield _api
    _api.destroy_db()


@pytest.fixture(scope="function", name="populated_housekeeper_api")
def fixture_populated_housekeeper_api(housekeeper_api, bundle_data):
    """Setup Housekeeper store."""
    _api = housekeeper_api
    bundle_obj, version_obj = _api.add_bundle(bundle_data)
    _api.add_commit(bundle_obj, version_obj)
    return _api


@pytest.fixture(name="a_date")
def fixture_a_date() -> datetime.datetime:
    """Return a datetime object with a date"""

    return datetime.datetime(2020, 5, 1)


@pytest.fixture(name="later_date")
def fixture_later_date() -> datetime.datetime:
    """Return a datetime object with a date later than a_date"""

    return datetime.datetime(2020, 5, 3)


@pytest.fixture(name="minimal_bundle_obj")
def fixture_minimal_bundle_obj(a_date, case_id, housekeeper_api) -> models.Bundle:
    """Return a bundle object with minimal information (name and created_at)"""
    _bundle_obj = housekeeper_api.new_bundle(name=case_id, created_at=a_date)

    return _bundle_obj


@pytest.fixture(name="tags")
def fixture_tags() -> list:
    """Return a list of housekeeper tags"""
    return ["bed"]


@pytest.fixture(name="bundle_data")
def fixture_bundle_data(a_date, case_id, bed_file, tags) -> dict:
    """Return a dictionary with bundle info in the correct format"""
    _bundle_data = {
        "name": case_id,
        "created": a_date,
        "files": [{"path": bed_file, "archive": False, "tags": tags}],
    }

    return _bundle_data
