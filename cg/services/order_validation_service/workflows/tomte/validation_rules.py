from cg.services.order_validation_service.validators.data_validators import (
    validate_customer_can_skip_reception_control,
    validate_user_customer_association,
)
from cg.services.order_validation_service.validators.inter_field_validators import (
    validate_ticket_number_required_if_connected,
)


TOMTE_VALIDATION_RULES = [
    validate_ticket_number_required_if_connected,
    validate_user_customer_association,
    validate_customer_can_skip_reception_control,
]
