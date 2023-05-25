from sqlalchemy.orm import Query
from cg.store import Store
from cg.store.models import Invoice
from tests.store_helpers import StoreHelpers
from cg.store.filters.status_invoice_filters import (
    filter_invoices_by_invoice_id,
    filter_invoices_invoiced,
    filter_invoices_not_invoiced,
)
from tests.store.conftest import StoreConstants


def test_filter_get_invoices_by_invoice_id(
    store_with_an_invoice_with_and_without_attributes: Store,
    entry_id=StoreConstants.INVOICE_ID_INVOICE_WITH_ATTRIBUTES.value,
):
    """Test to get invoice by invoice id."""

    # GIVEN an Store with two invoices

    # WHEN getting invoice by invoice id
    invoice: Query = filter_invoices_by_invoice_id(
        invoices=store_with_an_invoice_with_and_without_attributes._get_query(table=Invoice),
        entry_id=entry_id,
    )

    # THEN assert that the invoice is a Query
    assert isinstance(invoice, Query)

    # THEN assert that the invoice is returned
    assert invoice.all() and len(invoice.all()) == 1


def test_filter_get_invoices_invoiced(store_with_an_invoice_with_and_without_attributes: Store):
    """Test to get invoice by invoice id."""

    # GIVEN an Store with two invoices of which one is invoiced

    # WHEN getting invoice by invoice id
    invoice: Query = filter_invoices_invoiced(
        invoices=store_with_an_invoice_with_and_without_attributes._get_query(table=Invoice)
    )

    # THEN assert that the invoice is a query
    assert isinstance(invoice, Query)

    # THEN assert that the invoice is returned
    assert invoice.all() and len(invoice.all()) == 1


def test_filter_get_invoices_not_invoiced(
    store_with_an_invoice_with_and_without_attributes: Store, helpers: StoreHelpers
):
    """Test to get invoice by invoice id."""

    # GIVEN a Store with two invoices of which one is invoiced

    # WHEN getting invoice by invoice id
    invoice: Query = filter_invoices_not_invoiced(
        invoices=store_with_an_invoice_with_and_without_attributes._get_query(table=Invoice)
    )

    # THEN assert that the invoice is a query
    assert isinstance(invoice, Query)

    # THEN assert that the invoice is returned
    assert invoice.all() and len(invoice.all()) == 1
