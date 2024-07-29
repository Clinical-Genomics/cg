from cg.services.order_validation_service.validators.data.rules import (
    validate_customer_can_skip_reception_control,
    validate_customer_exists,
    validate_user_belongs_to_customer,
)
from cg.services.order_validation_service.validators.inter_field.rules import (
    validate_ticket_number_required_if_connected,
)
from cg.services.order_validation_service.workflows.tomte.validation.inter_field.rules import (
    validate_no_repeated_case_names,
    validate_no_repeated_sample_names,
    validate_wells_contain_at_most_one_sample,
)

TOMTE_ORDER_RULES = [
    validate_customer_exists,
    validate_user_belongs_to_customer,
    validate_ticket_number_required_if_connected,
    validate_customer_can_skip_reception_control,
]

TOMTE_CASE_SAMPLE_RULES = [
    validate_no_repeated_case_names,
    validate_no_repeated_sample_names,
    validate_wells_contain_at_most_one_sample,
]
