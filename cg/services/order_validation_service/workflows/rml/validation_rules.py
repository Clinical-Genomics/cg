from cg.services.order_validation_service.rules.sample.rules import (
    validate_application_compatibility,
    validate_application_exists,
    validate_applications_not_archived,
    validate_container_name_required,
    validate_sample_names_available,
    validate_sample_names_unique,
    validate_volume_interval,
    validate_volume_required,
    validate_well_position_format,
    validate_well_positions_required,
)

SAMPLE_RULES: list[callable] = [
    validate_application_compatibility,
    validate_application_exists,
    validate_applications_not_archived,
    validate_container_name_required,
    validate_sample_names_available,
    validate_sample_names_unique,
    validate_volume_interval,
    validate_volume_required,
    validate_well_position_format,
    validate_well_positions_required,
]
