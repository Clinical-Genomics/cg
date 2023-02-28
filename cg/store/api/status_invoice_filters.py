from typing import Optional, List
from enum import Enum
from sqlalchemy.orm import Query
from cg.store.models import Invoice


class InvoiceFilters(str, Enum):
    get_invoice_by_id = ("get_invoice_by_id",)
    get_invoice_by_invoice_id = "get_invoice_by_invoice_id"
    get_invoice_by_customer_id = "get_invoice_by_customer_id"
    get_invoice_by_customer_name = "get_invoice_by_customer_name"
    get_invoice_invoiced = "get_invoice_invoiced"
    get_invoice_not_invoiced = "get_invoice_not_invoiced"


def get_invoice_by_invoice_id(invoices: Query, invoice_id: int) -> Query:
    """Filter invoices by invoice_id"""
    return invoices.filter(Invoice.id == invoice_id)


def get_invoice_by_customer_id(invoices: Query, customer_id: int) -> Query:
    """Filter invoices by customer_id"""
    return invoices.filter(Invoice.customer_id == customer_id)


def get_invoice_by_customer_name(invoices: Query, customer_name: str) -> Query:
    """Filter invoices by customer_name"""
    return invoices.filter(Invoice.customer.name == customer_name)


def get_invoice_invoiced(invoices: Query) -> Query:
    """Filter invoices by invoiced_at"""
    return invoices.filter(Invoice.invoiced_at.isnot(None))


def get_invoice_not_invoiced(invoices: Query) -> Query:
    """Filter invoices by not invoiced_at"""
    return invoices.filter(Invoice.invoiced_at.is_(None))


def apply_sample_filter(
    functions: List[str],
    invoices: Query,
) -> Query:
    """Apply filtering functions to the invoice queries and return filtered results."""
    filter_map = {
        InvoiceFilters.get_invoice_by_invoice_id: get_invoice_by_invoice_id,
        InvoiceFilters.get_invoice_by_customer_id: get_invoice_by_customer_id,
        InvoiceFilters.get_invoice_by_customer_name: get_invoice_by_customer_name,
        InvoiceFilters.get_invoice_invoiced: get_invoice_invoiced,
        InvoiceFilters.get_invoice_not_invoiced: get_invoice_not_invoiced,
    }

    for function in functions:
        invoices: Query = filter_map[function](invoices=invoices)
    return invoices
