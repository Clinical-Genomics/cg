from enum import Enum
from typing import List, Optional, Callable

from sqlalchemy.orm import Query

from cg.store.models import Customer


def filter_customer_by_customer_internal_id(customers: Query, customer_id: str, **kwargs) -> Query:
    """Return customer by customer internal id."""
    return customers.filter(Customer.internal_id == customer_id)


class CustomerFilter(Enum):
    """Define customer filter functions."""

    FILTER_BY_INTERNAL_ID: Callable = filter_customer_by_customer_internal_id


def apply_customer_filter(
    customers: Query,
    filter_functions: List[Callable],
    customer_id: Optional[str] = None,
) -> Query:
    """Apply filtering functions and return filtered results."""
    for filter_function in filter_functions:
        customers: Query = filter_function(
            customers=customers,
            customer_id=customer_id,
        )
    return customers
