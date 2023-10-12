"""Fixtures for deliver commands"""

from pathlib import Path

import pytest
from housekeeper.store.models import Version

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.delivery import INBOX_NAME
from cg.models.cg_config import CGConfig
from cg.store import Store
from tests.store_helpers import StoreHelpers

# Paths


@pytest.fixture
def delivery_inbox(project_dir: Path, customer_id: Path, ticket_id: str) -> Path:
    return Path(project_dir, customer_id, INBOX_NAME, ticket_id)


@pytest.fixture
def deliver_vcf_path(delivery_inbox: Path, family_name: str, case_id: str, vcf_file: Path) -> Path:
    return Path(delivery_inbox, family_name, vcf_file.name.replace(case_id, family_name))


@pytest.fixture
def deliver_fastq_path(delivery_inbox: Path, cust_sample_id: str) -> Path:
    return Path(delivery_inbox, cust_sample_id, "dummy_run_R1_001.fastq.gz")


@pytest.fixture
def base_context(
    base_context: CGConfig, project_dir: Path, real_housekeeper_api: HousekeeperAPI
) -> CGConfig:
    base_context.housekeeper_api_ = real_housekeeper_api
    base_context.delivery_path: str = project_dir.as_posix()
    return base_context


@pytest.fixture
def mip_delivery_bundle(
    case_hk_bundle_no_files: dict,
    sample_cram_files: list[Path],
    sample_ids: list[str],
    vcf_file: Path,
) -> dict:
    """Return a bundle that includes files used when delivering MIP analysis data"""
    case_hk_bundle_no_files["files"] = [
        {"path": str(vcf_file), "archive": False, "tags": ["vcf-snv-clinical"]},
    ]
    for index, sample_id in enumerate(sample_ids):
        case_hk_bundle_no_files["files"].append(
            {"path": str(sample_cram_files[index]), "archive": False, "tags": [sample_id, "cram"]}
        )
    return case_hk_bundle_no_files


@pytest.fixture
def fastq_delivery_bundle(
    sample_hk_bundle_no_files: dict, fastq_file: Path, sample_id: str
) -> dict:
    """Return a sample bundle that includes a fastq file"""
    sample_hk_bundle_no_files["name"] = sample_id
    sample_hk_bundle_no_files["files"] = [
        {"path": str(fastq_file), "archive": False, "tags": ["fastq", "deliver", "ADM1"]},
    ]
    return sample_hk_bundle_no_files


@pytest.fixture
def mip_dna_housekeeper(
    real_housekeeper_api: HousekeeperAPI,
    mip_delivery_bundle: dict,
    fastq_delivery_bundle: dict,
    helpers: StoreHelpers,
) -> HousekeeperAPI:
    helpers.ensure_hk_bundle(real_housekeeper_api, bundle_data=mip_delivery_bundle)
    helpers.ensure_hk_bundle(real_housekeeper_api, bundle_data=fastq_delivery_bundle)
    # assert that the files exists
    version_obj_mip: Version = real_housekeeper_api.last_version(mip_delivery_bundle["name"])
    version_obj_fastq: Version = real_housekeeper_api.last_version(fastq_delivery_bundle["name"])
    real_housekeeper_api.include(version_obj=version_obj_mip)
    real_housekeeper_api.include(version_obj=version_obj_fastq)

    return real_housekeeper_api


@pytest.fixture
def populated_mip_context(
    base_context: CGConfig,
    analysis_store: Store,
    mip_dna_housekeeper: HousekeeperAPI,
    project_dir: Path,
) -> CGConfig:
    base_context.housekeeper_api_ = mip_dna_housekeeper
    base_context.status_db_ = analysis_store
    base_context.delivery_path: str = project_dir.as_posix()
    return base_context


@pytest.fixture
def context_with_missing_bundle(
    cg_context: CGConfig,
    analysis_store: Store,
    mip_dna_housekeeper: HousekeeperAPI,
    project_dir: Path,
    helpers: StoreHelpers,
    ticket_id: str,
) -> CGConfig:
    cg_context.housekeeper_api_ = mip_dna_housekeeper
    helpers.add_case(store=analysis_store, ticket=ticket_id)
    cg_context.status_db_ = analysis_store
    cg_context.delivery_path: str = project_dir.as_posix()
    return cg_context
