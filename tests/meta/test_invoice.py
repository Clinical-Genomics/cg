import mock
import pytest
from tests.store_helpers import StoreHelpers
from cg.meta.invoice import InvoiceAPI
from tests.mocks.limsmock import MockLimsAPI
from cg.store import Store
from cg.constants.invoice import CostCenters, CustomerNames
from cg.constants.sequencing import RecordType
from cg.constants.priority import PriorityTerms
from cg.store.models import Pool, Sample

from cg.models.invoice.invoice import InvoiceInfo


@pytest.fixture(name="get_invoice_api_sample")
def fixture_invoice_api_sample(
    store: Store,
    lims_api: MockLimsAPI,
    helpers: StoreHelpers,
    invoice_id: int = 0,
    record_type: str = RecordType.Sample,
    customer_id: str = CustomerNames.cust132,
) -> InvoiceAPI:
    """Return an InvoiceAPI."""
    invoice = helpers.ensure_invoice(
        store,
        invoice_id=invoice_id,
        record_type=record_type,
        customer_id=customer_id,
    )
    api = InvoiceAPI(store, lims_api, invoice)
    return api


@pytest.fixture(name="get_invoice_api_nipt_customer")
def fixture_invoice_api_nipt_customer(
    store: Store,
    lims_api: MockLimsAPI,
    helpers: StoreHelpers,
    invoice_id: int = 0,
    record_type: str = RecordType.Pool,
    customer_id: str = CustomerNames.cust032,
) -> InvoiceAPI:
    """Return an InvoiceAPI."""
    invoice = helpers.ensure_invoice(
        store,
        invoice_id=invoice_id,
        record_type=record_type,
        customer_id=customer_id,
    )
    api = InvoiceAPI(store, lims_api, invoice)
    return api


@pytest.fixture(name="get_invoice_api_pool_generic_customer")
def fixture_invoice_api_pool_generic_customer(
    store: Store,
    lims_api: MockLimsAPI,
    helpers: StoreHelpers,
    invoice_id: int = 0,
    record_type: str = RecordType.Pool,
    customer_id: str = CustomerNames.cust132,
) -> InvoiceAPI:
    """Return an InvoiceAPI."""
    invoice = helpers.ensure_invoice(
        store,
        invoice_id=invoice_id,
        record_type=record_type,
        customer_id=customer_id,
    )
    api = InvoiceAPI(store, lims_api, invoice)
    return api


def test_assert_invoice_api(get_invoice_api_sample):
    # ASSERT that an API can be initiated
    assert isinstance(get_invoice_api_sample, InvoiceAPI)


def test_assert_invoice_api(get_invoice_api_sample):
    # GIVEN an invoice API
    api = get_invoice_api_sample
    # THEN a report should be generated
    report = api.get_invoice_report("KI")


def test_invoice_api_sample(get_invoice_api_sample, record_type: str = "Sample"):
    """Test that the invoice records the right record_type"""
    # THEN calling InvoiceAPI should return an API
    api = get_invoice_api_sample
    assert api
    # THEN record_type should be Sample
    assert api.record_type == record_type
    # THEN prepare_invoice_report should set priority to standard
    api.get_invoice_report(CostCenters.ki)
    assert api.invoice_info.priority == PriorityTerms.STANDARD

    # THEN get_invoice_report returns a dictionary
    invoice_dict = api.get_invoice_report(CostCenters.ki)
    assert type(invoice_dict) == dict

    # THEN prepare_invoice_report should set priority to standard
    assert api.invoice_info.priority == PriorityTerms.STANDARD

    # THEN raw.records should contain a Pool
    assert type(api.raw_records[0]) == Sample

    # THEN api holds an InvoiceInfo class
    assert type(api.invoice_info) == InvoiceInfo


def test_invoice_api_nipt_customer(get_invoice_api_nipt_customer, record_type: str = "Pool"):
    # GIVEN an invoice api with NIPT customer
    api = get_invoice_api_nipt_customer

    # THEN record_type should be a Pool
    api.genologics_lims = mock.MagicMock()
    assert api.record_type == record_type

    # THEN get_invoice_report returns a dictionary
    invoice_dict = api.get_invoice_report(CostCenters.ki)
    assert type(invoice_dict) == dict

    # THEN prepare_invoice_report should set priority to standard
    assert api.invoice_info.priority == PriorityTerms.STANDARD

    # THEN raw.records should contain a Pool
    assert type(api.raw_records[0]) == Pool

    # THEN api holds an InvoiceInfo class
    assert type(api.invoice_info) == InvoiceInfo


def test_invoice_pool_generic_customer(
    get_invoice_api_pool_generic_customer, record_type: str = RecordType.Pool
):
    # GIVEN an invoice API with a pool and a generic customer
    api = get_invoice_api_pool_generic_customer
    assert api
    # THEN record_type should be Pool
    api.genologics_lims = mock.MagicMock()
    assert api.record_type == record_type
    # THEN prepare_invoice_report should set priority to research
    api.get_invoice_report(CostCenters.ki)
    assert api.invoice_info.priority == PriorityTerms.RESEARCH
