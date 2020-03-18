"""Fixtures for testing apps"""
from datetime import datetime

import pytest
from cg.apps.hk import HousekeeperAPI


@pytest.yield_fixture(scope="function")
def store_housekeeper(tmpdir):
    """Setup Housekeeper store."""
    root_path = tmpdir.mkdir("bundles")
    _store = HousekeeperAPI(
        {"housekeeper": {"database": "sqlite://", "root": str(root_path)}}
    )
    _store.create_all()
    yield _store
    _store.drop_all()
