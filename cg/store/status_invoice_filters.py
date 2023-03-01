from typing import Optional, List, Callable
from enum import Enum
from sqlalchemy.orm import Query
from cg.store.models import Invoice


def get_invoice_by_invoice_id(invoices: Query, invoice_id: int, **kwargs) -> Query:
    """Filter invoices by invoice_id"""
    return invoices.filter(Invoice.id == invoice_id)


def get_invoice_invoiced(invoices: Query, **kwargs) -> Query:
    """Filter invoices by invoiced_at"""
    return invoices.filter(Invoice.invoiced_at.isnot(None))


def get_invoice_not_invoiced(invoices: Query, **kwargs) -> Query:
    """Filter invoices by not invoiced_at"""
    return invoices.filter(Invoice.invoiced_at.is_(None))


def apply_invoice_filter(
    functions: List[str],
    invoices: Query,
) -> Query:
    """Apply filtering functions to the invoice queries and return filtered results."""

    for function in functions:
        invoices: Query = function(invoices=invoices)
    return invoices


class InvoiceFilters(Enum):
    get_invoice_by_id: Callable = get_invoice_by_invoice_id
    get_invoice_invoiced: Callable = get_invoice_invoiced
    get_invoice_not_invoiced: Callable = get_invoice_not_invoiced
