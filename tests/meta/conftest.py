"""Fixtures for the meta tests"""

from datetime import datetime

import pytest

from cg.constants.tags import HkMipAnalysisTag
from tests.store_helpers import StoreHelpers

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI
from cg.store import Store


@pytest.fixture(scope="function", name="analysis_store")
def fixture_analysis_store(base_store: Store, analysis_family: dict) -> Store:
    """Setup a store instance for testing analysis API."""
    customer = base_store.customer("cust000")
    family = base_store.Family(
        data_analysis=analysis_family["data_analysis"],
        name=analysis_family["name"],
        panels=analysis_family["panels"],
        internal_id=analysis_family["internal_id"],
        priority="standard",
    )
    family.customer = customer
    base_store.add(family)
    application_version = base_store.application("WGTPCFC030").versions[0]
    for sample_data in analysis_family["samples"]:
        sample = base_store.add_sample(
            name=sample_data["name"],
            sex=sample_data["sex"],
            internal_id=sample_data["internal_id"],
            ticket=sample_data["ticket_number"],
            reads=sample_data["reads"],
            capture_kit=sample_data["capture_kit"],
        )
        sample.family = family
        sample.application_version = application_version
        sample.customer = customer
        base_store.add(sample)
    base_store.commit()
    for sample_data in analysis_family["samples"]:
        sample_obj = base_store.sample(sample_data["internal_id"])
        link = base_store.relate_sample(
            family=family,
            sample=sample_obj,
            status=sample_data["status"],
            father=base_store.sample(sample_data["father"]) if sample_data.get("father") else None,
            mother=base_store.sample(sample_data["mother"]) if sample_data.get("mother") else None,
        )
        base_store.add(link)
    base_store.commit()
    yield base_store


@pytest.fixture(scope="function", name="mip_hk_store")
def fixture_mip_hk_store(
    helpers: StoreHelpers,
    real_housekeeper_api: HousekeeperAPI,
    timestamp: datetime,
    case_id: str,
) -> HousekeeperAPI:
    deliver_hk_bundle_data = {
        "name": case_id,
        "created": timestamp,
        "expires": timestamp,
        "files": [
            {
                "path": "tests/fixtures/apps/mip/dna/store/case_config.yaml",
                "archive": False,
                "tags": ["mip-config"],
            },
            {
                "path": "tests/fixtures/apps/mip/dna/store/case_qc_sample_info.yaml",
                "archive": False,
                "tags": ["sampleinfo"],
            },
            {
                "path": "tests/fixtures/apps/mip/case_metrics_deliverables.yaml",
                "archive": False,
                "tags": [HkMipAnalysisTag.QC_METRICS],
            },
            {
                "path": "tests/fixtures/apps/mip/case_file.txt",
                "archive": False,
                "tags": ["case-tag"],
            },
            {
                "path": "tests/fixtures/apps/mip/sample_file.txt",
                "archive": False,
                "tags": ["sample-tag", "ADM1"],
            },
        ],
    }
    helpers.ensure_hk_bundle(real_housekeeper_api, deliver_hk_bundle_data, include=True)

    empty_deliver_hk_bundle_data = {
        "name": "case_missing_data",
        "created": timestamp,
        "expires": timestamp,
        "files": [
            {
                "path": "tests/fixtures/apps/mip/dna/store/empty_case_config.yaml",
                "archive": False,
                "tags": ["mip-config"],
            },
            {
                "path": "tests/fixtures/apps/mip/dna/store/empty_case_qc_sample_info.yaml",
                "archive": False,
                "tags": ["sampleinfo"],
            },
            {
                "path": "tests/fixtures/apps/mip/dna/store/empty_case_metrics_deliverables.yaml",
                "archive": False,
                "tags": [HkMipAnalysisTag.QC_METRICS],
            },
            {
                "path": "tests/fixtures/apps/mip/case_file.txt",
                "archive": False,
                "tags": ["case-tag"],
            },
            {
                "path": "tests/fixtures/apps/mip/sample_file.txt",
                "archive": False,
                "tags": ["sample-tag", "ADM1"],
            },
        ],
    }
    helpers.ensure_hk_bundle(real_housekeeper_api, empty_deliver_hk_bundle_data, include=True)

    return real_housekeeper_api


@pytest.fixture()
def mip_analysis_api(context_config, mip_hk_store, analysis_store):
    analysis_api = MipDNAAnalysisAPI(context_config)
    analysis_api.housekeeper_api = mip_hk_store
    analysis_api.status_db = analysis_store
    return analysis_api
