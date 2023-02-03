from tests.store_helpers import StoreHelpers
from cg.meta.invoice import InvoiceAPI
from cg.apps.lims import api as limsAPI
import cg.store as Store


def test_invoice_api(store: Store, lims_api: limsAPI, helpers: StoreHelpers):
    # GIVEN a invoice
    invoice = helpers.add_invoice(store, type="Sample", customer_id="cust032")
    # GIVEN customer in store
    customer_obj = helpers.ensure_customer(store, customer_id="cust032")
    store.add_user(customer=customer_obj, email="test@testing.com", name="tester", is_admin=False)

    # THEN calling InvoiceAPI should return an API
    api = InvoiceAPI(store, lims_api, invoice)
    assert api
    # THEN prepare should return customer information with customer id cust999
    kth_inv = api.prepare("KTH")
    assert kth_inv["customer_id"] == "cust032"
