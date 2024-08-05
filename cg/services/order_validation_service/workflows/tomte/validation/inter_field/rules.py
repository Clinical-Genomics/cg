from cg.services.order_validation_service.models.errors import (
    FatherNotInCaseError,
    InvalidConcentrationIfSkipRCError,
    InvalidFatherSexError,
    InvalidMotherSexError,
    MotherNotInCaseError,
    OccupiedWellError,
    PedigreeError,
    RepeatedCaseNameError,
    RepeatedSampleNameError,
    SubjectIdSameAsCaseNameError,
)
from cg.services.order_validation_service.workflows.tomte.models.order import TomteOrder
from cg.services.order_validation_service.workflows.tomte.validation.inter_field.pedigree.validate_pedigree import (
    get_pedigree_errors,
)
from cg.services.order_validation_service.workflows.tomte.validation.inter_field.utils import (
    _get_errors,
    _get_excess_samples,
    _get_plate_samples,
    get_father_case_errors,
    get_father_sex_errors,
    get_mother_case_errors,
    get_mother_sex_errors,
    get_repeated_case_name_errors,
    get_repeated_sample_name_errors,
    validate_concentration_in_case,
    validate_subject_ids_in_case,
)
from cg.store.store import Store


def validate_wells_contain_at_most_one_sample(order: TomteOrder) -> list[OccupiedWellError]:
    samples_with_cases = _get_plate_samples(order)
    samples = _get_excess_samples(samples_with_cases)
    return _get_errors(samples)


def validate_case_names_not_repeated(order: TomteOrder) -> list[RepeatedCaseNameError]:
    return get_repeated_case_name_errors(order)


def validate_sample_names_not_repeated(order: TomteOrder) -> list[RepeatedSampleNameError]:
    errors: list[RepeatedSampleNameError] = []
    for case in order.cases:
        case_errors = get_repeated_sample_name_errors(case)
        errors.extend(case_errors)
    return errors


def validate_fathers_are_male(order: TomteOrder) -> list[InvalidFatherSexError]:
    errors: list[InvalidFatherSexError] = []
    for case in order.cases:
        case_errors = get_father_sex_errors(case)
        errors.extend(case_errors)
    return errors


def validate_fathers_in_same_case_as_children(order: TomteOrder) -> list[FatherNotInCaseError]:
    errors = []
    for case in order.cases:
        case_errors = get_father_case_errors(case)
        errors.extend(case_errors)
    return errors


def validate_mothers_are_female(order: TomteOrder) -> list[InvalidMotherSexError]:
    errors: list[InvalidMotherSexError] = []
    for case in order.cases:
        case_errors = get_mother_sex_errors(case)
        errors.extend(case_errors)
    return errors


def validate_pedigree(order: TomteOrder) -> list[PedigreeError]:
    errors = []
    for case in order.cases:
        case_errors = get_pedigree_errors(case)
        errors.extend(case_errors)
    return errors


def validate_mothers_in_same_case_as_children(order: TomteOrder) -> list[MotherNotInCaseError]:
    errors = []
    for case in order.cases:
        case_errors = get_mother_case_errors(case)
        errors.extend(case_errors)
    return errors


def validate_subject_ids_different_from_case_names(
    order: TomteOrder,
) -> list[SubjectIdSameAsCaseNameError]:
    errors = []
    for case in order.cases:
        case_errors = validate_subject_ids_in_case(case)
        errors.extend(case_errors)
    return errors


def validate_concentration_interval_if_skip_rc(
    order: TomteOrder, store: Store
) -> list[InvalidConcentrationIfSkipRCError]:
    if not order.skip_reception_control:
        return []
    errors = []
    for case in order.cases:
        case_errors = validate_concentration_in_case(case=case, store=store)
        errors.extend(case_errors)
    return errors
