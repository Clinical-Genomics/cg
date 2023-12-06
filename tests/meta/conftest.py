"""Fixtures for the meta tests."""
import datetime as dt
from datetime import datetime
from pathlib import Path
from typing import Generator

import pytest

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.constants import CustomerId
from cg.constants.housekeeper_tags import HkMipAnalysisTag
from cg.constants.sequencing import Sequencers
from cg.meta.invoice import InvoiceAPI
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI
from cg.store import Store
from cg.store.models import ApplicationVersion, Customer, Invoice, Sample
from tests.mocks.limsmock import MockLimsAPI
from tests.store_helpers import StoreHelpers


@pytest.fixture(scope="function")
def mip_hk_store(
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
                "tags": HkMipAnalysisTag.QC_METRICS,
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
                "tags": HkMipAnalysisTag.QC_METRICS,
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


@pytest.fixture
def mip_analysis_api(context_config, mip_hk_store, analysis_store):
    """Return a MIP analysis API."""
    analysis_api = MipDNAAnalysisAPI(context_config)
    analysis_api.housekeeper_api = mip_hk_store
    analysis_api.status_db = analysis_store
    return analysis_api


@pytest.fixture
def binary_path() -> str:
    """Return the string of a path to a (fake) binary."""
    return Path("usr", "bin", "binary").as_posix()


@pytest.fixture
def stats_sample_data(
    sample_id: str,
    bcl2fastq_flow_cell_id: str,
    bcl_convert_flow_cell_id: str,
) -> dict:
    return {
        "samples": [
            {
                "name": sample_id,
                "index": "ACGTACAT",
                "flowcell": bcl2fastq_flow_cell_id,
                "type": Sequencers.NOVASEQ,
            },
            {
                "name": "ADM1136A3",
                "index": "ACGTACAT",
                "flowcell": bcl_convert_flow_cell_id,
                "type": Sequencers.NOVASEQ,
            },
        ]
    }


@pytest.fixture
def flowcell_store(base_store: Store, stats_sample_data: dict) -> Generator[Store, None, None]:
    """Setup store with sample data for testing flow cell transfer."""
    for sample_data in stats_sample_data["samples"]:
        customer: Customer = (base_store.get_customers())[0]
        application_version: ApplicationVersion = base_store.get_application_by_tag(
            "WGSPCFC030"
        ).versions[0]
        sample: Sample = base_store.add_sample(
            name="NA", sex="male", internal_id=sample_data["name"]
        )
        sample.customer = customer
        sample.application_version = application_version
        sample.received_at = dt.datetime.now()
        sample.last_sequenced_at = dt.datetime.now()
        base_store.session.add(sample)
    base_store.session.commit()
    yield base_store


@pytest.fixture
def get_invoice_api_sample(
    store: Store,
    lims_api: MockLimsAPI,
    helpers: StoreHelpers,
    invoice_id: int = 0,
    customer_id: str = CustomerId.CUST132,
) -> InvoiceAPI:
    """Return an InvoiceAPI with samples."""
    sample = helpers.add_sample(store, customer_id=customer_id)
    invoice: Invoice = helpers.ensure_invoice(
        store,
        invoice_id=invoice_id,
        customer_id=customer_id,
        samples=[sample],
    )
    return InvoiceAPI(store, lims_api, invoice)


@pytest.fixture(name="get_invoice_api_nipt_customer")
def invoice_api_nipt_customer(
    store: Store,
    lims_api: MockLimsAPI,
    helpers: StoreHelpers,
    invoice_id: int = 0,
    customer_id: str = CustomerId.CUST032,
) -> InvoiceAPI:
    """Return an InvoiceAPI with a pool for NIPT customer."""
    pool = helpers.ensure_pool(store=store, customer_id=customer_id)
    invoice: Invoice = helpers.ensure_invoice(
        store,
        invoice_id=invoice_id,
        customer_id=customer_id,
        pools=[pool],
    )
    return InvoiceAPI(store, lims_api, invoice)


@pytest.fixture(name="get_invoice_api_pool_generic_customer")
def invoice_api_pool_generic_customer(
    store: Store,
    lims_api: MockLimsAPI,
    helpers: StoreHelpers,
    invoice_id: int = 0,
    customer_id: str = CustomerId.CUST132,
) -> InvoiceAPI:
    """Return an InvoiceAPI with a pool."""
    pool = helpers.ensure_pool(store=store, customer_id=customer_id)
    invoice: Invoice = helpers.ensure_invoice(
        store,
        invoice_id=invoice_id,
        pools=[pool],
        customer_id=customer_id,
    )
    return InvoiceAPI(store, lims_api, invoice)
