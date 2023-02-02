from tests.store_helpers import StoreHelpers
from cg.meta.invoice import InvoiceAPI
from cg.apps.lims import api as limsAPI
import cg.store as Store


def test_invoice_api(store: Store, lims_api: limsAPI, helpers: StoreHelpers):
    # GIVEN a invoice
    invoice = helpers.add_invoice(store, type="Sample", customer_id="cust032")

    # THEN calling InvoiceAPI should return an API
    api = InvoiceAPI(store, lims_api, invoice)
    assert api

    # THEN prepare
    kth_inv = api.prepare("KTH")
    print(kth_inv)
