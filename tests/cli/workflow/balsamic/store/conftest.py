"""Fixtures for cli balsamic tests"""
from datetime import datetime
from pathlib import Path

import pytest

from cg.apps.hk import HousekeeperAPI
from cg.apps.tb import TrailblazerAPI
from cg.store import Store, models


@pytest.fixture
def balsamic_store_context(
    balsamic_store, balsamic_case, housekeeper_api, hk_bundle_data, helpers
) -> dict:
    """context to use in cli"""

    hk_bundle_data["name"] = balsamic_case.internal_id
    print("Here", balsamic_case.internal_id)
    print(hk_bundle_data)
    bundle = helpers.ensure_hk_bundle(housekeeper_api, hk_bundle_data)
    print(bundle)
    print(bundle.__dict__)
    return {
        "hk_api": housekeeper_api,
        "db": balsamic_store,
        "tb_api": MockTB(),
        "balsamic": {"root": "root", "conda_env": "conda_env"},
    }


class MockTB(TrailblazerAPI):
    """Mock of trailblazer """

    def __init__(self):
        """Override TrailblazerAPI __init__ to avoid default behaviour"""

    def analyses(
        self,
        *,
        family: str = None,
        query: str = None,
        status: str = None,
        deleted: bool = None,
        temp: bool = False,
        before: datetime = None,
        is_visible: bool = None,
        workflow=None
    ):
        """Override TrailblazerAPI analyses method to avoid default behaviour"""
        return []


class MockHouseKeeper(HousekeeperAPI):
    """Mock HousekeeperAPI"""

    def __init__(self, bundle_name):
        """Override HousekeeperAPI method to avoid default behaviour"""
        self._store = MockHousekeeperStore()
        self.bundle_name = bundle_name
        self.bundle_data = None
        self.root_dir = "root_dir"

    def get_files(self, bundle: str, tags: list, version: int = None):
        """return a list of mocked files"""
        del tags, bundle, version
        return [MockFile()]

    def add_bundle(self, data: dict):
        """fake adding a bundle in housekeeper"""

        if not self.bundle_data or self.bundle_data["name"] != data["name"]:
            self.bundle_data = data
            return MockBundle(data=data, name=self.bundle_name), MockVersion()

        return None


class MockHousekeeperStore:
    """Mock Store of Housekeeper"""

    def __init__(self):
        """Override __init__ to avoid default behaviour"""
        self.root_dir = ""

    def add_commit(self, *pargs, **kwargs):
        """Implements add_commit to allow it to be used in HousekeeperAPI"""


class MockBundle:
    """Mock Bundle"""

    def __init__(self, data, name):
        """Implement minimal set of properties to allow it to be used in test"""
        self.name = name
        self._data = data


class MockVersion:
    """Mock Version"""

    def __init__(self):
        """Implement minimal set of properties to allow it to be used in test"""
        self.created_at = datetime.now()
        self.included_at = None
        self.relative_root_dir = ""
        self.files = []


class MockFile:
    """Mock File"""

    def __init__(self, path=""):
        """Implement minimal set of properties to allow it to be used in test"""
        self.path = path
        self.full_path = path


@pytest.fixture(name="balsamic_dir")
def fixture_balsamic_dir(apps_dir: Path) -> Path:
    """Return the path to the balsamic apps dir"""
    return apps_dir / "balsamic"


@pytest.fixture(name="balsamic_case_dir")
def fixture_balsamic_case_dir(balsamic_dir: Path) -> Path:
    """Return the path to the balsamic apps case dir"""
    return balsamic_dir / "case"


@pytest.fixture(scope="function")
def deliverables_file(balsamic_case_dir):
    """Return a balsamic deliverables file"""
    return str(balsamic_case_dir / "metadata.yml")


@pytest.fixture(scope="function")
def deliverables_file_directory(balsamic_case_dir):
    """Return a balsamic deliverables file containing a directory"""
    return str(balsamic_case_dir / "metadata_directory.yml")


@pytest.fixture(scope="function")
def deliverables_file_tags(balsamic_case_dir):
    """Return a balsamic deliverables file containing one file with two tags"""
    return str(balsamic_case_dir / "metadata_file_tags.yml")
