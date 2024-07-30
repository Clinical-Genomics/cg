from cg.constants.subject import Sex
from cg.services.order_validation_service.models.errors import (
    FatherNotInCaseError,
    InvalidFatherSexError,
    InvalidMotherSexError,
    OccupiedWellError,
    RepeatedCaseNameError,
    RepeatedSampleNameError,
    SampleIsOwnFatherError,
    SampleIsOwnMotherError,
)
from cg.services.order_validation_service.workflows.tomte.models.order import TomteOrder
from cg.services.order_validation_service.workflows.tomte.models.sample import TomteSample
from cg.services.order_validation_service.workflows.tomte.validation.inter_field.utils import (
    get_sample_is_own_father_errors,
    get_sample_is_own_mother_errors,
    get_well_errors,
    _get_excess_samples,
    get_plate_samples,
    get_father_case_errors,
    get_father_sex_errors,
    get_mother_sex_errors,
    get_repeated_case_name_errors,
    get_repeated_sample_name_errors,
)


def validate_wells_contain_at_most_one_sample(order: TomteOrder) -> list[OccupiedWellError]:
    samples_with_cases = get_plate_samples(order)
    samples = _get_excess_samples(samples_with_cases)
    return get_well_errors(samples)


def validate_no_repeated_case_names(order: TomteOrder) -> list[RepeatedCaseNameError]:
    return get_repeated_case_name_errors(order)


def validate_no_repeated_sample_names(order: TomteOrder) -> list[RepeatedSampleNameError]:
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


def validate_sample_is_not_own_mother(order: TomteOrder) -> list[SampleIsOwnMotherError]:
    errors: list[SampleIsOwnMotherError] = []
    for case in order.cases:
        case_errors = get_sample_is_own_mother_errors(case)
        errors.extend(case_errors)
    return errors


def validate_sample_is_not_own_father(order: TomteOrder) -> list[SampleIsOwnFatherError]:
    errors: list[SampleIsOwnFatherError] = []
    for case in order.cases:
        case_errors = get_sample_is_own_father_errors(case)
        errors.extend(case_errors)
    return errors
