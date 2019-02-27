"""Test fixtures for housekeeper tests"""
import pytest
from cg.apps.hk.api import HousekeeperAPI


@pytest.yield_fixture(scope='function')
def hk_api(tmpdir):
    """Setup Housekeeper store."""
    root_path = tmpdir.mkdir('bundles')
    _store = HousekeeperAPI({'housekeeper': {'database': 'sqlite://', 'root': str(root_path)}})
    _store.create_all()
    yield _store
    _store.drop_all()
