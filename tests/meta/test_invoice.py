import mock
from tests.store_helpers import StoreHelpers
from cg.meta.invoice import InvoiceAPI
from tests.mocks.limsmock import MockLimsAPI

from cg.store import Store, models
from cg.constants.record_type import RecordType
from cg.constants.priority import PriorityTerms


def test_invoice_api_sample(
    store: Store,
    lims_api: MockLimsAPI,
    helpers: StoreHelpers,
    invioce_id: int = 0,
    record_type: str = RecordType.Sample,
    customer_id: str = "cust032",
):
    # GIVEN an invoice
    invoice = helpers.ensure_invoice(
        store,
        invoice_id=invioce_id,
        record_type=record_type,
        customer_id=customer_id,
    )

    # THEN calling InvoiceAPI should return an API
    api = InvoiceAPI(store, lims_api, invoice)
    assert api
    # THEN record_type should be Sample
    assert api.record_type == record_type
    # THEN prepare should return customer information with customer id cust999

    cust032_inv: dict = api.prepare("ki")
    assert cust032_inv["customer_id"] == customer_id


def test_invoice_api_pool_cust032(
    store: Store,
    lims_api: MockLimsAPI,
    helpers: StoreHelpers,
    invoice_id: int = 0,
    record_type: str = RecordType.Pool,
    customer_id: str = "cust032",
):
    # GIVEN a invoice
    invoice = helpers.ensure_invoice(
        store,
        invoice_id=invoice_id,
        record_type=record_type,
        customer_id=customer_id,
    )

    # THEN calling InvoiceAPI should return an API
    api = InvoiceAPI(store, lims_api, invoice)
    assert api
    # THEN record_type should be Sample
    api.genologics_lims = mock.MagicMock()
    assert api.record_type == record_type
    # THEN prepare should return customer information with customer id cust999
    api.prepare("ki")
    assert api.invoice_info["priority"] == PriorityTerms.STANDARD


def test_invoice_pool_generic_customer(
    store: Store,
    lims_api: MockLimsAPI,
    helpers: StoreHelpers,
    invoice_id: int = 0,
    record_type: str = RecordType.Pool,
    customer_id: str = "cust132",
):

    invoice = helpers.ensure_invoice(
        store,
        invoice_id=invoice_id,
        record_type=record_type,
        customer_id=customer_id,
    )

    # THEN calling InvoiceAPI should return an API
    api = InvoiceAPI(store, lims_api, invoice)
    assert api
    # THEN record_type should be Sample
    api.genologics_lims = mock.MagicMock()
    assert api.record_type == record_type
    # THEN prepare should return customer information with customer id cust999
    api.prepare("ki")
    assert api.invoice_info["priority"] == PriorityTerms.RESEARCH
