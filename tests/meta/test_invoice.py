import mock
import pytest

import cg.meta.invoice
from tests.store_helpers import StoreHelpers
from cg.meta.invoice import InvoiceAPI
from tests.mocks.limsmock import MockLimsAPI

from cg.store import Store, models
from cg.constants.record_type import RecordType
from cg.constants.priority import PriorityTerms


def test_assert_invoice_api(
    store: Store,
    lims_api: MockLimsAPI,
    helpers: StoreHelpers,
    invoice_id: int = 0,
    record_type: str = RecordType.Sample,
    customer_id: str = "cust001",
):
    # GIVEN an invoice
    invoice = helpers.ensure_invoice(
        store,
        invoice_id=invoice_id,
        record_type=record_type,
        customer_id=customer_id,
    )
    api = InvoiceAPI(store, lims_api, invoice)
    assert isinstance(api, InvoiceAPI)


def test_prepare(
    store: Store,
    lims_api: MockLimsAPI,
    helpers: StoreHelpers,
    invoice_id: int = 0,
    record_type: str = RecordType.Sample,
    customer_ids: [str] = ["cust032", "cust999", "cust542"],
    costcenters: [str] = ["kth", "ki"],
):
    """Tests that get_customer returns the right customer objects or string"""
    # GIVEN an invoice with customer_id
    for customer_id in customer_ids:
        for costcenter in costcenters:
            invoice = helpers.ensure_invoice(
                store,
                invoice_id=invoice_id,
                record_type=record_type,
                customer_id=customer_id,
            )
            api = InvoiceAPI(store, lims_api, invoice)
            api.prepare(costcenter=costcenter)
            # THEN get_customer with costcenter "kth" should always return cust999 customer obejct
            if costcenter == "kth":
                assert api.get_customer(costcenter=costcenter).internal_id == "cust999"
            # THEN get_customer with costcenter "ki" should return a models.Costumer with the supplied customer_id
            elif costcenter == "ki":
                assert api.get_customer(costcenter=costcenter).internal_id == customer_id


def test_invoice_api_sample(
    store: Store,
    lims_api: MockLimsAPI,
    helpers: StoreHelpers,
    invoice_id: int = 0,
    record_type: str = RecordType.Sample,
    customer_id: str = "cust032",
):
    """Test that the invoice records the right record_type"""
    # GIVEN an invoice
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
    assert api.record_type == record_type
    # THEN prepare should set an invoice_info dictionary
    api.prepare("ki")


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
    # THEN record_type should be a Pool
    api.genologics_lims = mock.MagicMock()
    assert api.record_type == record_type

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
