from cg.services.order_validation_service.workflows.microsalt.validation.data.rules import (
    validate_application_exists,
    validate_applications_not_archived,
    validate_buffer_required,
    validate_organism_exists,
    validate_samples_exist,
    validate_volume_interval,
)
from cg.services.order_validation_service.workflows.microsalt.validation.inter_field.rules import (
    validate_application_compatibility,
    validate_sample_names_unique,
    validate_well_positions_required,
    validate_wells_contain_at_most_one_sample,
)


SAMPLE_RULES: list[callable] = [
    validate_application_compatibility,
    validate_application_exists,
    validate_applications_not_archived,
    validate_buffer_required,
    validate_organism_exists,
    validate_sample_names_unique,
    validate_samples_exist,
    validate_volume_interval,
    validate_well_positions_required,
    validate_wells_contain_at_most_one_sample,
]
