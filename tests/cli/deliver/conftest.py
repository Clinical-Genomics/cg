"""Fixtures for deliver commands"""

from pathlib import Path

import pytest

from cg.store import Store
from cg.apps.hk import HousekeeperAPI

from housekeeper.store import models as hk_models

from tests.store_helpers import StoreHelpers


# Paths


@pytest.fixture(name="delivery_inbox")
def fixture_delivery_inbox(project_dir: Path, customer_id: Path, ticket_nr: int) -> Path:
    return project_dir / customer_id / "inbox" / str(ticket_nr)


@pytest.fixture(name="deliver_vcf_path")
def fixture_deliver_vcf_path(
    delivery_inbox: Path, family_name: str, case_id: str, vcf_file: Path
) -> Path:
    return delivery_inbox / family_name / vcf_file.name.replace(case_id, family_name)


@pytest.fixture(name="base_context")
def fixture_base_context(
    base_store: Store, real_housekeeper_api: HousekeeperAPI, project_dir: Path
) -> dict:
    return {
        "status_db": base_store,
        "housekeeper_api": real_housekeeper_api,
        "delivery_path": str(project_dir),
    }


@pytest.fixture(name="mip_delivery_bundle")
def fixture_mip_delivery_bundle(
    case_hk_bundle_no_files: dict, sample1_cram: Path, vcf_file: Path
) -> dict:
    """Return a bundle that includes files used when delivering MIP analysis data"""
    case_hk_bundle_no_files["files"] = [
        {"path": str(sample1_cram), "archive": False, "tags": ["ADM1", "cram"]},
        {"path": str(vcf_file), "archive": False, "tags": ["vcf-snv-clinical"]},
    ]
    return case_hk_bundle_no_files


@pytest.fixture(name="mip_dna_housekeeper")
def fixture_mip_dna_housekeeper(
    real_housekeeper_api: HousekeeperAPI, mip_delivery_bundle: dict, helpers: StoreHelpers
) -> HousekeeperAPI:
    helpers.ensure_hk_bundle(real_housekeeper_api, bundle_data=mip_delivery_bundle)
    # assert that the files exists
    version_obj: hk_models.Version = real_housekeeper_api.last_version(mip_delivery_bundle["name"])
    real_housekeeper_api.include(version_obj=version_obj)

    return real_housekeeper_api


@pytest.fixture(name="populated_mip_context")
def fixture_populated_mip_context(
    analysis_store: Store, mip_dna_housekeeper: HousekeeperAPI, project_dir: Path
) -> dict:
    return {
        "status_db": analysis_store,
        "housekeeper_api": mip_dna_housekeeper,
        "delivery_path": str(project_dir),
    }
