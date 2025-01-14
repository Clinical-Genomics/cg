from cg.services.order_validation_service.rules.case.rules import (
    validate_case_internal_ids_exist,
    validate_case_names_available,
    validate_case_names_not_repeated,
)
from cg.services.order_validation_service.rules.case_sample.rules import (
    validate_application_compatibility,
    validate_application_exists,
    validate_application_not_archived,
    validate_buffer_required,
    validate_buffer_skip_rc_condition,
    validate_concentration_interval_if_skip_rc,
    validate_concentration_required_if_skip_rc,
    validate_container_name_required,
    validate_sample_names_different_from_case_names,
    validate_sample_names_not_repeated,
    validate_samples_exist,
    validate_subject_ids_different_from_case_names,
    validate_subject_ids_different_from_sample_names,
    validate_subject_sex_consistency,
    validate_tube_container_name_unique,
    validate_volume_interval,
    validate_volume_required,
    validate_well_position_format,
    validate_well_positions_required,
    validate_wells_contain_at_most_one_sample,
)
from cg.services.order_validation_service.workflows.balsamic.rules import (
    validate_capture_kit_panel_requirement,
)

BALSAMIC_CASE_RULES: list[callable] = [
    validate_case_internal_ids_exist,
    validate_case_names_available,
    validate_case_names_not_repeated,
]

BALSAMIC_CASE_SAMPLE_RULES: list[callable] = [
    validate_application_compatibility,
    validate_application_exists,
    validate_application_not_archived,
    validate_buffer_required,
    validate_buffer_skip_rc_condition,
    validate_capture_kit_panel_requirement,
    validate_volume_required,
    validate_concentration_interval_if_skip_rc,
    validate_concentration_required_if_skip_rc,
    validate_container_name_required,
    validate_samples_exist,
    validate_sample_names_different_from_case_names,
    validate_sample_names_not_repeated,
    validate_subject_sex_consistency,
    validate_subject_ids_different_from_case_names,
    validate_subject_ids_different_from_sample_names,
    validate_tube_container_name_unique,
    validate_volume_interval,
    validate_well_position_format,
    validate_well_positions_required,
    validate_wells_contain_at_most_one_sample,
]
