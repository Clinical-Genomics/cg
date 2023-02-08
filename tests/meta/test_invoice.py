import mock
from tests.store_helpers import StoreHelpers
from cg.meta.invoice import InvoiceAPI
from tests.mocks.limsmock import MockLimsAPI
from cg.server.ext import lims as genologics_lims

from cg.store import Store, models



def return_samples_in_pools_mock():
    pass

def test_invoice_api_sample(store: Store, lims_api: MockLimsAPI, helpers: StoreHelpers):
    # GIVEN a invoice
    invoice = helpers.ensure_invoice(
        store,
        invoice_id=0,
        record_type="Sample",
        customer_id="cust032",
    )

    # THEN calling InvoiceAPI should return an API
    api = InvoiceAPI(store, lims_api, invoice)
    assert api
    # THEN record_type should be Sample
    assert api.record_type == "Sample"
    # THEN prepare should return customer information with customer id cust999

    cust032_inv: dict = api.prepare("ki")
    assert cust032_inv["customer_id"] == "cust032"


def test_invoice_api_pool(store: Store, lims_api: MockLimsAPI, helpers: StoreHelpers):
    # GIVEN a invoice
    invoice_cust032 = helpers.ensure_invoice(
        store,
        invoice_id=0,
        record_type="Pool",
        customer_id="cust032",
    )

    # THEN calling InvoiceAPI should return an API
    api_cust032 = InvoiceAPI(store, lims_api, invoice_cust032)
    assert api_cust032
    # THEN record_type should be Sample
    api_cust032.genologics_lims = mock.MagicMock()
    assert api_cust032.record_type == "Pool"
    # THEN prepare should return customer information with customer id cust999
    api_cust032.prepare("ki")
    assert api_cust032.invoice_info["priority"] == "standard"

    invoice_cust032 = helpers.ensure_invoice(
        store,
        invoice_id=0,
        record_type="Pool",
        customer_id="cust132",
    )

    # THEN calling InvoiceAPI should return an API
    api_cust132 = InvoiceAPI(store, lims_api, invoice_cust132)
    assert api_cust132
    # THEN record_type should be Sample
    api_cust132.genologics_lims = mock.MagicMock()
    assert api_cust132.record_type == "Pool"
    # THEN prepare should return customer information with customer id cust999
    api_cust132.prepare("ki")
    assert api_cust132.invoice_info["priority"] == "research"
