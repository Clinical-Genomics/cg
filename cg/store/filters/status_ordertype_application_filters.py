from enum import Enum

from sqlalchemy.orm import Query

from cg.models.orders.constants import OrderType
from cg.store.models import OrderTypeApplication


def filter_applications_by_order_type(
    order_type_applications: Query, order_type: OrderType, **kwargs
) -> Query:
    """Return application by order type."""
    return order_type_applications.filter(OrderTypeApplication.order_type == order_type)


def apply_order_type_application_filter(
    filter_functions: list[callable],
    order_type_applications: Query,
    order_type: OrderType = None,
) -> Query:
    """Apply filtering functions to the ordertype_applications query and return filtered results."""

    for filter_function in filter_functions:
        order_type_applications: Query = filter_function(
            order_type_applications=order_type_applications,
            order_type=order_type,
        )
    return order_type_applications


class OrderTypeApplicationFilter(Enum):
    """Define OrderTypeApplication filter functions."""

    BY_ORDER_TYPE = filter_applications_by_order_type
