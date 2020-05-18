"""Fixtures for the housekeeper tests"""

import datetime

import pytest
from housekeeper.store import models

from cg.apps.hk import HousekeeperAPI


@pytest.fixture(name="hk_config")
def fixture_hk_config(root_path) -> dict:
    """Return a dictionary with housekeeper api configs for testing"""
    configs = {
        "housekeeper": {"database": "sqlite:///:memory:", "root": str(root_path)}
    }
    return configs


@pytest.yield_fixture(scope="function", name="housekeeper_api")
def fixture_housekeeper_api(hk_config):
    """Setup Housekeeper store."""
    _api = HousekeeperAPI(hk_config)
    _api.initialise_db()
    yield _api
    _api.destroy_db()


@pytest.fixture(name="a_date")
def fixture_a_date() -> datetime.datetime:
    """Return a datetime object with a date"""

    return datetime.datetime(2020, 5, 1)


@pytest.fixture(name="empty_bundle_obj")
def fixture_empty_bundle_obj(a_date, case_id, housekeeper_api) -> models.Bundle:
    """Return a bundle object with minimal information"""
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
