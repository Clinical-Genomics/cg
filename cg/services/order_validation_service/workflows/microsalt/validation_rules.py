from cg.services.order_validation_service.validators.data.rules import (
    validate_customer_can_skip_reception_control,
    validate_customer_exists,
    validate_user_belongs_to_customer,
)
from cg.services.order_validation_service.validators.inter_field.rules import (
    validate_ticket_number_required_if_connected,
)
from cg.services.order_validation_service.workflows.microsalt.validation.data.rules import (
    validate_application_exists,
    validate_applications_not_archived,
    validate_samples_exist,
)
from cg.services.order_validation_service.workflows.microsalt.validation.inter_field.rules import (
    validate_application_compatibility,
    validate_sample_names_unique,
    validate_well_positions_required,
    validate_wells_contain_at_most_one_sample,
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
    validate_applications_not_archived,
    validate_sample_names_unique,
    validate_samples_exist,
    validate_well_positions_required,
    validate_wells_contain_at_most_one_sample,
]
