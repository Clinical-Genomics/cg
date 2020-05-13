"""Fixtures for the housekeeper tests"""

import pytest

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
