from cg.services.order_validation_service.models.order import Order


def _is_order_name_required(order: Order) -> bool:
    return False if order.connect_to_ticket else not order.name


def _is_ticket_number_missing(order: Order) -> bool:
    return order.connect_to_ticket and not order.ticket_number
