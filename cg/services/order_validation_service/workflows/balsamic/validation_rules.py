from cg.services.order_validation_service.rules.case.rules import (
    validate_case_internal_ids_exist,
    validate_case_names_available,
    validate_case_names_not_repeated,
)
from cg.services.order_validation_service.rules.case_sample.rules import (
    validate_application_compatibility,
    validate_application_exists,
    validate_application_not_archived,
    validate_buffer_skip_rc_condition,
    validate_concentration_interval_if_skip_rc,
    validate_concentration_required_if_skip_rc,
    validate_sample_names_not_repeated,
    validate_samples_exist,
    validate_sex_required_for_new_samples,
    validate_source_required,
    validate_status_required_if_new,
    validate_subject_ids_different_from_case_names,
    validate_subject_ids_different_from_sample_names,
    validate_volume_interval,
    validate_wells_contain_at_most_one_sample,
)

CASE_RULES: list[callable] = [
    validate_case_internal_ids_exist,
    validate_case_names_available,
    validate_case_names_not_repeated,
]

CASE_SAMPLE_RULES: list[callable] = [
    validate_application_compatibility,
    validate_application_exists,
    validate_application_not_archived,
    validate_buffer_skip_rc_condition,
    validate_concentration_interval_if_skip_rc,
    validate_concentration_required_if_skip_rc,
    validate_samples_exist,
    validate_sample_names_not_repeated,
    validate_sex_required_for_new_samples,
    validate_source_required,
    validate_status_required_if_new,
    validate_subject_ids_different_from_case_names,
    validate_subject_ids_different_from_sample_names,
    validate_volume_interval,
    validate_wells_contain_at_most_one_sample,
]
