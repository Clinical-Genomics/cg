from alchy import Query
from typing import List
from datetime import datetime
from cg.store import Store
from cg.store.models import Invoice
from tests.store_helpers import StoreHelpers
from cg.store.status_invoice_filters import (
    get_invoice_by_invoice_id,
    get_invoice_invoiced,
    get_invoice_not_invoiced,
)


def test_filter_get_invoice_by_invoice_id(
    base_store: Store, helpers: StoreHelpers, invoice_id: List[int] = [1, 2]
):

    """Test to get invoice by invoice id."""

    # GIVEN an Store with two invoices
    helpers.ensure_invoice(base_store, invoice_id=invoice_id[0])
    helpers.ensure_invoice(base_store, invoice_id=invoice_id[1])

    # ASSERT that there are two invoices
    assert base_store._get_invoices().count() == 2

    # GIVEN an invoice query
    invoices: Query = base_store._get_invoice_query()

    # WHEN getting invoice by invoice id
    invoice: List[Invoice] = list(
        get_invoice_by_invoice_id(invoices=invoices, invoice_id=invoice_id[0])
    )

    # THEN assert that the invoice is returned
    assert invoice and len(invoice) == 1


def test_filter_get_invoice_invoiced(base_store: Store, helpers: StoreHelpers):

    """Test to get invoice by invoice id."""

    # GIVEN an Store with two invoices
    helpers.ensure_invoice(base_store, invoiced_at=datetime.now(), invoice_id=1)
    helpers.ensure_invoice(base_store, invoiced_at=None, invoice_id=2)

    # ASSERT that there are two invoices
    assert base_store._get_invoices().count() == 2

    # GIVEN an invoice query
    invoices: Query = base_store._get_invoice_query()

    # WHEN getting invoice by invoice id
    invoice: List[Invoice] = list(get_invoice_invoiced(invoices=invoices))

    # THEN assert that the invoice is returned
    assert invoice and len(invoice) == 1


def test_filter_get_invoice_not_invoiced(base_store: Store, helpers: StoreHelpers):

    """Test to get invoice by invoice id."""

    # GIVEN an Store with two invoices
    helpers.ensure_invoice(base_store, invoiced_at=datetime.now(), invoice_id=1)
    helpers.ensure_invoice(base_store, invoiced_at=None, invoice_id=2)

    # ASSERT that there are two invoices
    assert base_store._get_invoices().count() == 2

    # GIVEN an invoice query
    invoices: Query = base_store._get_invoice_query()

    # WHEN getting invoice by invoice id
    invoice: List[Invoice] = list(get_invoice_not_invoiced(invoices=invoices))

    # THEN assert that the invoice is returned
    assert invoice and len(invoice) == 1
