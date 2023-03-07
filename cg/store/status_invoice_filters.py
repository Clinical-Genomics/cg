from typing import Optional, List, Callable
from enum import Enum
from sqlalchemy.orm import Query
from cg.store.models import Invoice


def filter_invoices_by_invoice_id(invoices: Query, invoice_id: int, **kwargs) -> Query:
    """Filter invoices by invoice_id."""
    return invoices.filter(Invoice.id == invoice_id)


def filter_invoices_invoiced(invoices: Query, **kwargs) -> Query:
    """Filter invoices by invoiced_at."""
    return invoices.filter(Invoice.invoiced_at.isnot(None))


def filter_invoices_not_invoiced(invoices: Query, **kwargs) -> Query:
    """Filter invoices by not invoiced_at."""
    return invoices.filter(Invoice.invoiced_at.is_(None))


def apply_invoice_filter(
    functions: List[str],
    invoices: Query,
    invoice_id: Optional[int] = None,
) -> Query:
    """Apply filtering functions to the invoice queries and return filtered results."""

    for function in functions:
        invoices: Query = function(invoices=invoices, invoice_id=invoice_id)
    return invoices


class InvoiceFilters(Enum):
    FILTER_BY_INVOICE_ID: Callable = filter_invoices_by_invoice_id
    FILTER_BY_INVOICED: Callable = filter_invoices_invoiced
    FILTER_BY_NOT_INVOICED: Callable = filter_invoices_not_invoiced
