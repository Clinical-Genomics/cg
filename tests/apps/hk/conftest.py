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
    print(3)
    if not _bundle:
        _bundle, _version = store.add_bundle(bundle_data)
        store.add_commit(_bundle, _version)
    print(3.1)
    return _bundle


def ensure_version(store: HousekeeperAPI, bundle_data):
    """utility function to return existing or create an version for tests"""
    print(2)
    _bundle = ensure_bundle(store, bundle_data)
    print(2.1)
    _version = store.last_version(_bundle)
    print(2.2)
    return _version


@pytest.yield_fixture(scope="function")
def version_obj(store_housekeeper, bundle_data):
    print(1)
    _version = ensure_version(store_housekeeper, bundle_data)
    print(1.1)
    return _version.ver
