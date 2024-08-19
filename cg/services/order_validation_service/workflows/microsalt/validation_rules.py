from cg.services.order_validation_service.validators.data.rules import (
    validate_application_exists,
    validate_application_not_archived,
    validate_customer_can_skip_reception_control,
    validate_customer_exists,
    validate_user_belongs_to_customer,
)
from cg.services.order_validation_service.validators.inter_field.rules import (
    validate_application_compatibility,
    validate_ticket_number_required_if_connected,
)

ORDER_RULES: list[callable] = [
    validate_customer_can_skip_reception_control,
    validate_customer_exists,
    validate_ticket_number_required_if_connected,
    validate_user_belongs_to_customer,
]
SAMPLE_RULES: list[callable] = [
    validate_application_compatibility,
    validate_application_exists,
    validate_application_not_archived,
]
