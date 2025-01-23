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
