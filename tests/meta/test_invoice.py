from tests.store_helpers import StoreHelpers
from cg.meta.invoice import InvoiceAPI
from cg.apps.lims import api as limsAPI
import cg.store as Store
from cg.store import models


def test_invoice_api(store: Store, lims_api: limsAPI, helpers: StoreHelpers):
    # GIVEN a invoice
    invoice = helpers.ensure_invoice(
        store,
        record_type="Sample",
        customer_id="cust032",
    )

    # THEN calling InvoiceAPI should return an API
    api = InvoiceAPI(store, lims_api, invoice)
    assert api
    # THEN prepare should return customer information with customer id cust999
    kth_inv = api.prepare("KTH")
    assert kth_inv["customer_id"] == "cust032"
