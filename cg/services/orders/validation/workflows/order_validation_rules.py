from cg.services.orders.validation.rules.order.rules import (
    validate_customer_can_skip_reception_control,
    validate_customer_exists,
    validate_user_belongs_to_customer,
)

ORDER_RULES: list[callable] = [
    validate_customer_can_skip_reception_control,
    validate_customer_exists,
    validate_user_belongs_to_customer,
]
