from cg.clients.freshdesk.constants import Status
from cg.models.orders.constants import OrderType
from cg.services.orders.constants import ORDER_TYPE_WORKFLOW_MAP
from cg.services.orders.validation.models.case import Case
from cg.services.orders.validation.models.order import Order
from cg.services.orders.validation.models.order_with_cases import OrderWithCases


def contains_existing_data(order: OrderWithCases) -> bool:
    """Check if the order contains any existing data"""

    for enumerated_case in order.enumerated_cases:
        case: Case = enumerated_case[1]
        if case.enumerated_existing_samples:
            return True
    return False


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
