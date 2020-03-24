"""Fixtures for testing apps"""
from datetime import datetime

import pytest
from cg.apps.hk import HousekeeperAPI


@pytest.yield_fixture(scope="function")
def store_housekeeper(tmpdir):
    """Setup Housekeeper store."""
    root_path = tmpdir.mkdir("bundles")
    _api = HousekeeperAPI({"housekeeper": {"database": "sqlite://", "root": str(root_path)}})
    _api.initialise_db()
    yield _api
    _api.destroy_db()


@pytest.yield_fixture(scope="function")
def file(bundle_data):
    return bundle_data["files"][0]["path"]


@pytest.fixture(scope="function")
def bundle_data():
    data = {
        "name": "sillyfish",
        "created": datetime.now(),
        "expires": datetime.now(),
        "files": [
            {
                "path": "tests/fixtures/analysis/sample_coverage.bed",
                "archive": False,
                "tags": ["bed", "sample"],
            }
        ],
    }
    return data


def ensure_bundle(store, bundle_data):
    _bundle = store.bundle(bundle_data["name"])
    if not _bundle:
        _bundle, _version = store.add_bundle(bundle_data)
        store.add_commit(_bundle, _version)
    return _bundle


def ensure_version(store: HousekeeperAPI, bundle_data):
    """utility function to return existing or create an version for tests"""
    _bundle = ensure_bundle(store, bundle_data)
    _version = store.last_version(_bundle)
    return _version


@pytest.yield_fixture(scope="function")
def version_obj(store_housekeeper, bundle_data):
    _version = ensure_version(store_housekeeper, bundle_data)
    return _version.ver
