from cg.services.order_validation_service.rules.order.order_rules import (
    validate_customer_can_skip_reception_control,
    validate_customer_exists,
    validate_ticket_number_required_if_connected,
    validate_user_belongs_to_customer,
)


ORDER_RULES: list[callable] = [
    validate_customer_can_skip_reception_control,
    validate_customer_exists,
    validate_ticket_number_required_if_connected,
    validate_user_belongs_to_customer,
]
