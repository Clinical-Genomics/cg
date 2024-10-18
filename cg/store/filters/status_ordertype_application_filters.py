from enum import Enum

from sqlalchemy.orm import Query

from cg.models.orders.constants import OrderType
from cg.store.models import OrderTypeApplication


def filter_applications_by_order_type(
    ordertype_applications: Query, order_type: OrderType, **kwargs
) -> Query:
    """Return application by order type."""
    return ordertype_applications.filter(OrderTypeApplication.order_type.is_(order_type))


def apply_order_type_application_filter(
    filter_functions: list[callable],
    ordertype_applications: Query,
    order_type: OrderType = None,
) -> Query:
    """Apply filtering functions to the ordertype_applications query and return filtered results."""

    for filter_function in filter_functions:
        ordertype_applications: Query = filter_function(
            applications_orders=ordertype_applications,
            order_type=order_type,
        )
    return ordertype_applications


class OrderTypeApplicationFilter(Enum):
    """Define OrderTypeApplication filter functions."""

    BY_ORDER_TYPE = filter_applications_by_order_type
