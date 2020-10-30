"""Fixtures for backup tests"""

from datetime import datetime
from pathlib import Path

import pytest

from cg.meta.deliver import DeliverAPI
from cg.store import Store
from cg.apps.hk import HousekeeperAPI


@pytest.yield_fixture(scope="function", name="deliver_api")
def fixture_deliver_api(
    analysis_store: Store, mip_hk_store: HousekeeperAPI, project_dir: Path
) -> DeliverAPI:
    """Fixture for deliver_api"""
    _deliver_api = DeliverAPI(
        store=analysis_store,
        hk_api=mip_hk_store,
        case_tags=["case-tag"],
        sample_tags=["sample-tag"],
        project_base_path=project_dir,
    )
    yield _deliver_api
