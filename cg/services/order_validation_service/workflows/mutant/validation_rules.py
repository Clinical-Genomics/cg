from cg.services.order_validation_service.rules.sample.rules import (
    validate_application_compatibility,
    validate_application_exists,
    validate_applications_not_archived,
    validate_container_name_required,
    validate_organism_exists,
    validate_sample_names_available,
    validate_tube_container_name_unique,
    validate_volume_interval,
    validate_volume_required,
    validate_well_position_format,
    validate_well_positions_required,
    validate_wells_contain_at_most_one_sample,
)
from cg.services.order_validation_service.workflows.mutant.rules import (
    validate_non_control_samples_are_unique,
)

MUTANT_SAMPLE_RULES: list[callable] = [
    validate_application_compatibility,
    validate_application_exists,
    validate_applications_not_archived,
    validate_container_name_required,
    validate_non_control_samples_are_unique,
    validate_organism_exists,
    validate_volume_required,
    validate_sample_names_available,
    validate_tube_container_name_unique,
    validate_volume_interval,
    validate_well_position_format,
    validate_well_positions_required,
    validate_wells_contain_at_most_one_sample,
]
