from datetime import date, datetime, timedelta

from cg.clients.freshdesk.constants import Status
from cg.constants.priority import Priority
from cg.models.orders.constants import OrderType
from cg.services.orders.constants import ORDER_TYPE_WORKFLOW_MAP
from cg.services.orders.validation.models.order import Order
from cg.services.orders.validation.models.order_with_cases import OrderWithCases

DUE_TIME_BY_PRIORITY: dict[Priority, timedelta.days] = {
    Priority.express: timedelta(days=7),
    Priority.priority: timedelta(days=14),
    Priority.standard: timedelta(days=21),
    Priority.clinical_trials: timedelta(days=21),
    Priority.research: timedelta(days=60),
}


def contains_existing_data(order: OrderWithCases) -> bool:
    """Check if the order contains any existing data"""
    return any(not case.is_new or case.enumerated_existing_samples for case in order.cases)


def get_ticket_tags(order: Order, order_type: OrderType) -> list[str]:
    """Generate ticket tags based on the order and order type"""

    tags: list[str] = [ORDER_TYPE_WORKFLOW_MAP[order_type]]

    if isinstance(order, OrderWithCases):
        if contains_existing_data(order):
            tags.append("existing-data")

    return tags


def contains_only_existing_samples(order: OrderWithCases) -> bool:
    """Check if the order contains only existing samples"""

    if order.enumerated_new_samples:
        return False
    return True


def get_ticket_status(order: Order) -> Status:
    """Get the ticket status based on the order"""

    if isinstance(order, OrderWithCases):
        if contains_only_existing_samples(order=order):
            return Status.OPEN
    return Status.PENDING


def get_due_by_date(priority: Priority) -> date:
    """Get the ticket due by date based on the order priority."""
    due_by: datetime = datetime.now() + DUE_TIME_BY_PRIORITY[priority]
    return due_by.date()
