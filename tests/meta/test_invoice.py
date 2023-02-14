import mock
import pytest

import cg.meta.invoice
from tests.store_helpers import StoreHelpers
from cg.meta.invoice import InvoiceAPI
from tests.mocks.limsmock import MockLimsAPI

from cg.store import Store
from cg.constants.invoice import Costcenters, CustomerNames, InvoiceInfo
from cg.constants.sequencing import RecordType
from cg.constants.priority import PriorityTerms


def test_assert_invoice_api(
    store: Store,
    lims_api: MockLimsAPI,
    helpers: StoreHelpers,
    invoice_id: int = 0,
    record_type: str = RecordType.Sample,
    customer_id: str = CustomerNames.cust001,
):
    # GIVEN an invoice
    invoice = helpers.ensure_invoice(
        store,
        invoice_id=invoice_id,
        record_type=record_type,
        customer_id=customer_id,
    )
    # ASSERT that an API can be initiated
    api = InvoiceAPI(store, lims_api, invoice)
    assert isinstance(api, InvoiceAPI)


def test_invoice_api_sample(
    store: Store,
    lims_api: MockLimsAPI,
    helpers: StoreHelpers,
    invoice_id: int = 0,
    record_type: str = RecordType.Sample,
    customer_id: str = CustomerNames.cust132,
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
    api.prepare(Costcenters.ki)
    assert api.invoice_info[InvoiceInfo.priority] == PriorityTerms.STANDARD


def test_invoice_api_pool_cust032(
    store: Store,
    lims_api: MockLimsAPI,
    helpers: StoreHelpers,
    invoice_id: int = 0,
    record_type: str = RecordType.Pool,
    customer_id: str = CustomerNames.cust032,
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
    # THEN prepare should set priority to standard
    api.prepare(Costcenters.ki)
    assert api.invoice_info[InvoiceInfo.priority] == PriorityTerms.STANDARD


def test_invoice_pool_generic_customer(
    store: Store,
    lims_api: MockLimsAPI,
    helpers: StoreHelpers,
    invoice_id: int = 0,
    record_type: str = RecordType.Pool,
    customer_id: str = CustomerNames.cust132,
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
    # THEN record_type should be Pool
    api.genologics_lims = mock.MagicMock()
    assert api.record_type == record_type
    # THEN prepare should set priority to research
    api.prepare(Costcenters.ki)
    assert api.invoice_info[InvoiceInfo.priority] == PriorityTerms.RESEARCH
