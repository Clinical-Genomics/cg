"""Fixtures for deliver commands"""

import pytest

from cg.store import Store
from cg.apps.hk import HousekeeperAPI


@pytest.fixture(name="base_context")
def fixture_base_context(base_store: Store, real_housekeeper_api: HousekeeperAPI) -> dict:
    return {"store": base_store, "hk_api": real_housekeeper_api}


@pytest.fixture(name="mip_delivery_bundle")
def fixture_mip_delivery_bundle(case_hk_bundle_no_files: dict) -> dict:
    """Return a bundle that includes files used when delivering MIP analysis data"""
    return {}


@pytest.fixture(name="populated_mip_context")
def fixture_populated_mip_context():
    return None
