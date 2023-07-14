"""Fixtures for backup tests."""
from pathlib import Path

import pytest
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.delivery import INBOX_NAME
from cg.constants.housekeeper_tags import AlignmentFileTag
from cg.meta.deliver import DeliverAPI
from cg.store import Store
from cg.store.models import Family
from tests.store_helpers import StoreHelpers


@pytest.fixture(scope="function", name="deliver_api")
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
        case_tags=[{"case-tag"}],
        sample_tags=[{AlignmentFileTag.CRAM}],
        project_base_path=project_dir,
        delivery_type="balsamic",
    )
    yield _deliver_api


@pytest.fixture(name="delivery_hk_api")
def fixture_delivery_hk_api(
    mip_delivery_bundle,
    real_housekeeper_api: HousekeeperAPI,
    helpers=StoreHelpers,
) -> HousekeeperAPI:
    """Fixture that returns a housekeeper database with delivery data"""

    helpers.ensure_hk_bundle(real_housekeeper_api, bundle_data=mip_delivery_bundle)
    return real_housekeeper_api


@pytest.fixture(name="populated_deliver_api")
def fixture_populated_deliver_api(
    analysis_store: Store, delivery_hk_api: HousekeeperAPI, project_dir: Path
) -> DeliverAPI:
    """Return a delivery api where housekeeper is populated with some files"""
    _deliver_api = DeliverAPI(
        store=analysis_store,
        hk_api=delivery_hk_api,
        case_tags=[{"case-tag"}],
        sample_tags=[{AlignmentFileTag.CRAM}],
        project_base_path=project_dir,
        delivery_type="balsamic",
    )
    return _deliver_api


@pytest.fixture(name="dummy_file_name")
def fixture_dummy_file_name() -> str:
    """Returns a dummy file name."""
    return "dummy_file_name"


@pytest.fixture(name="all_samples_in_inbox")
def fixture_all_samples_in_inbox(analysis_family, dummy_file_name: str, tmpdir_factory) -> Path:
    """Fixture that returns a customer inbox path with all samples delivered."""
    inbox = tmpdir_factory.mktemp(INBOX_NAME)
    for index in range(3):
        Path(inbox, analysis_family["samples"][index]["name"]).mkdir(exist_ok=True, parents=True)
        Path(inbox, analysis_family["samples"][index]["name"], dummy_file_name).touch(exist_ok=True)
    Path(inbox, analysis_family["name"]).mkdir(exist_ok=True, parents=True)
    Path(inbox, analysis_family["name"], dummy_file_name).touch(exist_ok=True)
    return Path(inbox)


@pytest.fixture(name="samples_missing_in_inbox")
def fixture_samples_missing_in_inbox(
    all_samples_in_inbox: Path,
    analysis_family: dict,
    dummy_file_name: str,
) -> Path:
    """Fixture that returns a customer inbox path with all samples delivered."""
    all_samples_in_inbox.joinpath(analysis_family["samples"][0]["name"], dummy_file_name).unlink()
    return Path(all_samples_in_inbox)


@pytest.fixture(name="deliver_api_destination_path")
def fixture_deliver_api_destination_path(customer_id: str, case: Family, ticket_id: str) -> Path:
    return Path(customer_id, INBOX_NAME, ticket_id, case.name)
