from cg.services.order_validation_service.validators.data.rules import (
    validate_application_exists,
    validate_application_not_archived,
    validate_customer_can_skip_reception_control,
    validate_customer_exists,
    validate_gene_panels_exist,
    validate_gene_panels_unique,
    validate_user_belongs_to_customer,
)
from cg.services.order_validation_service.validators.inter_field.rules import (
    validate_application_compatibility,
    validate_buffer_skip_rc_condition,
    validate_concentration_required_if_skip_rc,
    validate_ticket_number_required_if_connected,
)
from cg.services.order_validation_service.workflows.tomte.validation.inter_field.rules import (
    validate_case_names_not_repeated,
    validate_fathers_are_male,
    validate_fathers_in_same_case_as_children,
    validate_mothers_are_female,
    validate_mothers_in_same_case_as_children,
    validate_pedigree,
    validate_sample_names_not_repeated,
    validate_subject_ids_different_from_case_names,
    validate_wells_contain_at_most_one_sample,
)

TOMTE_ORDER_RULES = [
    validate_customer_can_skip_reception_control,
    validate_customer_exists,
    validate_ticket_number_required_if_connected,
    validate_user_belongs_to_customer,
]

TOMTE_CASE_RULES = [
    validate_gene_panels_exist,
    validate_gene_panels_unique,
]

TOMTE_CASE_SAMPLE_RULES = [
    validate_application_compatibility,
    validate_application_exists,
    validate_application_not_archived,
    validate_buffer_skip_rc_condition,
    validate_case_names_not_repeated,
    validate_concentration_required_if_skip_rc,
    validate_fathers_are_male,
    validate_fathers_in_same_case_as_children,
    validate_mothers_are_female,
    validate_mothers_in_same_case_as_children,
    validate_pedigree,
    validate_sample_names_not_repeated,
    validate_subject_ids_different_from_case_names,
    validate_wells_contain_at_most_one_sample,
]
