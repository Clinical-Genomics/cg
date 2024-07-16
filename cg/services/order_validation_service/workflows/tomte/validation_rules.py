from cg.services.order_validation_service.validators.data_validators import (
    validate_customer_can_skip_reception_control,
    validate_customer_exists,
    validate_user_belongs_to_customer,
)
from cg.services.order_validation_service.validators.inter_field_validators import (
    validate_ticket_number_required_if_connected,
)


TOMTE_VALIDATION_RULES = [
    validate_customer_exists,
    validate_ticket_number_required_if_connected,
    validate_user_belongs_to_customer,
    validate_customer_can_skip_reception_control,
]
