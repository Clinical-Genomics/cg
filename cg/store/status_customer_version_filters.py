from enum import Enum
from typing import List, Optional, Callable

from sqlalchemy.orm import Query

from cg.store.models import Customer


def get_customer_by_customer_id(customers: Query, customer_id: str, **kwargs) -> Query:
    """Return customer by customer internal id."""
    return customers.filter(Customer.internal_id == customer_id)


class CustomerFilters(Enum):
    """Define customer filter functions."""

    get_customer_by_customer_id: Callable = get_customer_by_customer_id


def apply_customer_filter(
    customers: Query,
    functions: List[Callable],
    customer_id: Optional[str] = None,
) -> Query:
    """Apply filtering functions and return filtered results."""
    for function in functions:
        customers: Query = function(
            customers=customers,
            customer_id=customer_id,
        )
    return customers
