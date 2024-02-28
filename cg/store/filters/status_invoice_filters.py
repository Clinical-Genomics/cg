from enum import Enum
from typing import Callable

from sqlalchemy.orm import Query

from cg.store.models import Invoice


def filter_invoices_by_invoice_id(invoices: Query, entry_id: int, **kwargs) -> Query:
    """Return invoices by invoice id."""
    return invoices.filter(Invoice.id == entry_id)


def filter_invoices_invoiced(invoices: Query, **kwargs) -> Query:
    """Return invoices by invoiced at."""
    return invoices.filter(Invoice.invoiced_at.isnot(None))


def filter_invoices_not_invoiced(invoices: Query, **kwargs) -> Query:
    """Return invoices by not invoiced at."""
    return invoices.filter(Invoice.invoiced_at.is_(None))


def apply_invoice_filter(
    filter_functions: list[str],
    invoices: Query,
    entry_id: int | None = None,
) -> Query:
    """Apply filtering functions to the invoice queries and return filtered results."""

    for filter_function in filter_functions:
        invoices: Query = filter_function(invoices=invoices, entry_id=entry_id)
    return invoices


class InvoiceFilter(Enum):
    """Define Invoice filter functions."""

    BY_INVOICE_ID: Callable = filter_invoices_by_invoice_id
    BY_INVOICED: Callable = filter_invoices_invoiced
    BY_NOT_INVOICED: Callable = filter_invoices_not_invoiced
