from enum import Enum
from typing import Callable

from sqlalchemy.orm import Query

from cg.store.models import Customer


def filter_customer_by_customer_internal_id(
    customers: Query, customer_internal_id: str, **kwargs
) -> Query:
    """Return customer by customer internal id."""
    return customers.filter(Customer.internal_id == customer_internal_id)


def filter_customer_by_exclude_customer_internal_id(
    customers: Query, exclude_customer_internal_id: str, **kwargs
) -> Query:
    """Return customer excluded by customer internal id."""
    return customers.filter(Customer.internal_id != exclude_customer_internal_id)


class CustomerFilter(Enum):
    """Define customer filter functions."""

    BY_INTERNAL_ID: Callable = filter_customer_by_customer_internal_id
    EXCLUDE_INTERNAL_ID: Callable = filter_customer_by_exclude_customer_internal_id


def apply_customer_filter(
    customers: Query,
    filter_functions: list[Callable],
    customer_internal_id: str | None = None,
    exclude_customer_internal_id: str | None = None,
) -> Query:
    """Apply filtering functions and return filtered results."""
    for filter_function in filter_functions:
        customers: Query = filter_function(
            customers=customers,
            customer_internal_id=customer_internal_id,
            exclude_customer_internal_id=exclude_customer_internal_id,
        )
    return customers
