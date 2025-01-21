from cg.services.orders.validation.rules.sample.rules import (
    validate_application_compatibility,
    validate_application_exists,
    validate_applications_not_archived,
    validate_container_name_required,
    validate_sample_names_available,
    validate_sample_names_unique,
    validate_tube_container_name_unique,
    validate_volume_required,
    validate_well_position_format,
    validate_well_positions_required,
    validate_wells_contain_at_most_one_sample,
)

PACBIO_LONG_READ_SAMPLE_RULES: list[callable] = [
    validate_application_compatibility,
    validate_application_exists,
    validate_applications_not_archived,
    validate_container_name_required,
    validate_sample_names_available,
    validate_sample_names_unique,
    validate_tube_container_name_unique,
    validate_volume_required,
    validate_wells_contain_at_most_one_sample,
    validate_well_position_format,
    validate_well_positions_required,
]
