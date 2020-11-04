"""Fixtures for backup tests"""

from datetime import datetime
from pathlib import Path

import pytest

from cg.meta.deliver import DeliverAPI
from cg.store import Store
from cg.apps.hk import HousekeeperAPI

from tests.store_helpers import StoreHelpers


@pytest.yield_fixture(scope="function", name="deliver_api")
def fixture_deliver_api(
    analysis_store: Store, real_housekeeper_api: HousekeeperAPI, project_dir: Path
) -> DeliverAPI:
    """Fixture for deliver_api

    The fixture will return a delivery api where the store is populated with a case with three individuals.
    The housekeeper database is empty
    """
    _deliver_api = DeliverAPI(
        store=analysis_store,
        hk_api=real_housekeeper_api,
        case_tags=["case-tag"],
        sample_tags=["sample-tag"],
        project_base_path=project_dir,
    )
    yield _deliver_api


@pytest.fixture(name="populated_deliver_api")
def fixture_populated_deliver_api(
    deliver_api: DeliverAPI,
    case_hk_bundle_no_files: dict,
    bed_file: str,
    vcf_file: Path,
    helpers=StoreHelpers,
) -> DeliverAPI:
    """Return a delivery api where housekeeper is populated with some files"""
    hk_api = deliver_api.hk_api
    case_hk_bundle_no_files["files"] = [
        {"path": bed_file, "archive": False, "tags": ["case-tag"]},
        {"path": str(vcf_file), "archive": False, "tags": ["sample-tag", "ADM1"]},
    ]
    helpers.ensure_hk_bundle(hk_api, bundle_data=case_hk_bundle_no_files)
    return deliver_api
