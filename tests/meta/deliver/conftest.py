"""Fixtures for backup tests"""

from pathlib import Path

import pytest
from tests.store_helpers import StoreHelpers

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.meta.deliver import DeliverAPI
from cg.store import Store


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
        sample_tags=[{"sample-tag"}],
        project_base_path=project_dir,
        delivery_type="balsamic",
    )
    yield _deliver_api


@pytest.fixture(name="delivery_hk_api")
def fixture_delivery_hk_api(
    case_hk_bundle_no_files: dict,
    sample1_cram: Path,
    vcf_file: Path,
    real_housekeeper_api: HousekeeperAPI,
    helpers=StoreHelpers,
) -> HousekeeperAPI:
    """Fixture that returns a housekeeper database with delivery data"""

    case_hk_bundle_no_files["files"] = [
        {"path": str(sample1_cram), "archive": False, "tags": ["cram", "ADM1"]},
        {"path": str(vcf_file), "archive": False, "tags": ["vcf-snv-clinical"]},
    ]
    helpers.ensure_hk_bundle(real_housekeeper_api, bundle_data=case_hk_bundle_no_files)
    return real_housekeeper_api


@pytest.fixture(name="populated_deliver_api")
def fixture_populated_deliver_api(
    analysis_store: Store, delivery_hk_api: HousekeeperAPI, project_dir: Path
) -> DeliverAPI:
    """Return a delivery api where housekeeper is populated with some files"""
    _deliver_api = DeliverAPI(
        store=analysis_store,
        hk_api=delivery_hk_api,
        case_tags=["case-tag"],
        sample_tags=["sample-tag"],
        project_base_path=project_dir,
        delivery_type="balsamic",
    )
    return _deliver_api


@pytest.fixture(name="all_samples_in_inbox")
def fixture_all_samples_in_inbox(tmpdir_factory) -> Path:
    """Fixture that returns a customer inbox path with all samples delivered"""
    inbox = tmpdir_factory.mktemp("inbox")
    Path(inbox, "sample1").mkdir(exist_ok=True, parents=True)
    Path(inbox, "sample2").mkdir(exist_ok=True, parents=True)
    Path(inbox, "case").mkdir(exist_ok=True, parents=True)
    Path(inbox, "sample1", "sample_file.txt").touch(exist_ok=True)
    Path(inbox, "sample2", "sample_file.txt").touch(exist_ok=True)
    Path(inbox, "case", "case_file.txt").touch(exist_ok=True)
    return Path(inbox)


@pytest.fixture(name="samples_missing_in_inbox")
def fixture_samples_missing_in_inbox(tmpdir_factory) -> Path:
    """Fixture that returns a customer inbox path with all samples delivered"""
    inbox = tmpdir_factory.mktemp("inbox")
    Path(inbox, "sample1").mkdir(exist_ok=True, parents=True)
    Path(inbox, "sample2").mkdir(exist_ok=True, parents=True)
    Path(inbox, "sample1", "sample_file.txt").touch(exist_ok=True)
    Path(inbox, "case_with_no_data").mkdir(exist_ok=True, parents=True)
    return Path(inbox)
